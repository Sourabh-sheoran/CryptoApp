from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from app.database import get_db
from app.auth import get_current_user
from app.market import fetch_coingecko_markets

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio & Trading"])

class TradeRequest(BaseModel):
    coin_id: str
    symbol: str
    name: str
    quantity: float = Field(gt=0, description="Quantity to buy or sell")
    price_usd: float = Field(gt=0, description="Live execution price per unit in USD")

class WatchlistRequest(BaseModel):
    coin_id: str
    symbol: str
    name: str

@router.get("/")
async def get_portfolio(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    cash_balance = current_user["virtual_balance_usd"]

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT coin_id, symbol, name, quantity, avg_buy_price_usd, total_invested_usd
            FROM portfolios
            WHERE user_id = ? AND quantity > 0
        """, (user_id,))
        holdings = [dict(row) for row in cursor.fetchall()]

        cursor.execute("""
            SELECT id, type, coin_id, symbol, quantity, price_usd, total_usd, timestamp
            FROM transactions
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 50
        """, (user_id,))
        transactions = [dict(row) for row in cursor.fetchall()]

    # Fetch live prices for held coins to calculate real-time current value & PnL
    live_markets = await fetch_coingecko_markets(currency="usd", limit=150)
    market_price_map = {coin["id"]: coin["current_price"] for coin in live_markets}
    market_price_map.update({coin["symbol"].lower(): coin["current_price"] for coin in live_markets})

    total_crypto_value = 0.0
    total_invested = 0.0
    enriched_holdings = []

    for h in holdings:
        cid = h["coin_id"]
        sym = h["symbol"].lower()
        live_price = market_price_map.get(cid, market_price_map.get(sym, h["avg_buy_price_usd"]))
        
        current_value = h["quantity"] * live_price
        invested = h["total_invested_usd"]
        pnl = current_value - invested
        pnl_pct = (pnl / invested * 100) if invested > 0 else 0.0

        total_crypto_value += current_value
        total_invested += invested

        enriched_holdings.append({
            **h,
            "current_price_usd": round(live_price, 4 if live_price < 10 else 2),
            "current_value_usd": round(current_value, 2),
            "pnl_usd": round(pnl, 2),
            "pnl_percentage": round(pnl_pct, 2)
        })

    net_worth = cash_balance + total_crypto_value
    overall_pnl = (net_worth - 50000.0)
    overall_pnl_pct = (overall_pnl / 50000.0) * 100

    return {
        "user": current_user,
        "summary": {
            "cash_balance_usd": round(cash_balance, 2),
            "total_crypto_value_usd": round(total_crypto_value, 2),
            "total_net_worth_usd": round(net_worth, 2),
            "total_invested_usd": round(total_invested, 2),
            "total_profit_loss_usd": round(overall_pnl, 2),
            "total_profit_loss_pct": round(overall_pnl_pct, 2),
            "initial_virtual_fund": 50000.0
        },
        "holdings": enriched_holdings,
        "recent_transactions": transactions
    }

@router.post("/buy")
def buy_crypto(trade: TradeRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    cost = trade.quantity * trade.price_usd

    with get_db() as conn:
        cursor = conn.cursor()
        # Verify balance
        cursor.execute("SELECT virtual_balance_usd FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        
        current_balance = float(row["virtual_balance_usd"])
        if current_balance < cost:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient funds! Order cost is ${cost:,.2f} USD, but your available cash is ${current_balance:,.2f} USD."
            )

        new_balance = current_balance - cost
        cursor.execute("UPDATE users SET virtual_balance_usd = ? WHERE id = ?", (new_balance, user_id))

        # Check existing holding
        cursor.execute("SELECT quantity, avg_buy_price_usd, total_invested_usd FROM portfolios WHERE user_id = ? AND coin_id = ?", (user_id, trade.coin_id))
        existing = cursor.fetchone()

        if existing:
            old_qty = float(existing["quantity"])
            old_invested = float(existing["total_invested_usd"])
            new_qty = old_qty + trade.quantity
            new_invested = old_invested + cost
            new_avg = new_invested / new_qty

            cursor.execute("""
                UPDATE portfolios
                SET quantity = ?, avg_buy_price_usd = ?, total_invested_usd = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND coin_id = ?
            """, (new_qty, new_avg, new_invested, user_id, trade.coin_id))
        else:
            cursor.execute("""
                INSERT INTO portfolios (user_id, coin_id, symbol, name, quantity, avg_buy_price_usd, total_invested_usd)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, trade.coin_id, trade.symbol.upper(), trade.name, trade.quantity, trade.price_usd, cost))

        # Record transaction
        cursor.execute("""
            INSERT INTO transactions (user_id, type, coin_id, symbol, quantity, price_usd, total_usd)
            VALUES (?, 'BUY', ?, ?, ?, ?, ?)
        """, (user_id, trade.coin_id, trade.symbol.upper(), trade.quantity, trade.price_usd, cost))

        conn.commit()

    return {
        "success": True,
        "message": f"Successfully bought {trade.quantity} {trade.symbol.upper()} for ${cost:,.2f} USD!",
        "new_balance_usd": round(new_balance, 2)
    }

@router.post("/sell")
def sell_crypto(trade: TradeRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    proceeds = trade.quantity * trade.price_usd

    with get_db() as conn:
        cursor = conn.cursor()
        # Check existing holding
        cursor.execute("SELECT quantity, avg_buy_price_usd, total_invested_usd FROM portfolios WHERE user_id = ? AND coin_id = ?", (user_id, trade.coin_id))
        existing = cursor.fetchone()

        if not existing or float(existing["quantity"]) < trade.quantity:
            avail = float(existing["quantity"]) if existing else 0.0
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient holdings! You requested to sell {trade.quantity} {trade.symbol.upper()}, but you currently hold {avail}."
            )

        old_qty = float(existing["quantity"])
        old_invested = float(existing["total_invested_usd"])
        avg_price = float(existing["avg_buy_price_usd"])

        new_qty = old_qty - trade.quantity
        if new_qty <= 1e-8:
            cursor.execute("DELETE FROM portfolios WHERE user_id = ? AND coin_id = ?", (user_id, trade.coin_id))
        else:
            new_invested = new_qty * avg_price
            cursor.execute("""
                UPDATE portfolios
                SET quantity = ?, total_invested_usd = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND coin_id = ?
            """, (new_qty, new_invested, user_id, trade.coin_id))

        # Update cash balance
        cursor.execute("SELECT virtual_balance_usd FROM users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        new_balance = float(user_row["virtual_balance_usd"]) + proceeds
        cursor.execute("UPDATE users SET virtual_balance_usd = ? WHERE id = ?", (new_balance, user_id))

        # Record transaction
        cursor.execute("""
            INSERT INTO transactions (user_id, type, coin_id, symbol, quantity, price_usd, total_usd)
            VALUES (?, 'SELL', ?, ?, ?, ?, ?)
        """, (user_id, trade.coin_id, trade.symbol.upper(), trade.quantity, trade.price_usd, proceeds))

        conn.commit()

    return {
        "success": True,
        "message": f"Successfully sold {trade.quantity} {trade.symbol.upper()} for ${proceeds:,.2f} USD!",
        "new_balance_usd": round(new_balance, 2)
    }

# Watchlist endpoints
@router.get("/watchlist")
async def get_watchlist(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT coin_id, symbol, name, added_at FROM watchlists WHERE user_id = ? ORDER BY added_at DESC", (user_id,))
        watchlist = [dict(row) for row in cursor.fetchall()]

    live_markets = await fetch_coingecko_markets(currency="usd", limit=100)
    market_map = {c["id"]: c for c in live_markets}

    enriched = []
    for item in watchlist:
        c = market_map.get(item["coin_id"], {})
        enriched.append({
            **item,
            "current_price": c.get("current_price", 0),
            "price_change_percentage_24h": c.get("price_change_percentage_24h", 0),
            "image": c.get("image", ""),
            "market_cap": c.get("market_cap", 0),
            "high_24h": c.get("high_24h", 0),
            "low_24h": c.get("low_24h", 0)
        })

    return enriched

@router.post("/watchlist")
def add_to_watchlist(req: WatchlistRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO watchlists (user_id, coin_id, symbol, name)
            VALUES (?, ?, ?, ?)
        """, (user_id, req.coin_id, req.symbol.upper(), req.name))
        conn.commit()
    return {"success": True, "message": f"{req.name} added to your watchlist"}

@router.delete("/watchlist/{coin_id}")
def remove_from_watchlist(coin_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM watchlists WHERE user_id = ? AND coin_id = ?", (user_id, coin_id))
        conn.commit()
    return {"success": True, "message": "Removed from watchlist"}
