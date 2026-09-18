import time
import httpx
import yfinance as yf
from fastapi import APIRouter, Query, HTTPException

router = APIRouter(prefix="/api/market", tags=["Market Data"])

# Simple memory cache to prevent API rate limits
CACHE = {}
CACHE_TTL = 45 # seconds

def get_cached(key: str):
    if key in CACHE:
        item, expire_time = CACHE[key]
        if time.time() < expire_time:
            return item
    return None

def set_cached(key: str, data, ttl: int = CACHE_TTL):
    CACHE[key] = (data, time.time() + ttl)

# Currency conversion rates fallback (USD, INR, EUR)
CURRENCY_RATES = {
    "usd": 1.0,
    "inr": 86.8,
    "eur": 0.92,
    "gbp": 0.78
}

COIN_TICKER_MAP = {
    "bitcoin": "BTC-USD",
    "ethereum": "ETH-USD",
    "solana": "SOL-USD",
    "binancecoin": "BNB-USD",
    "ripple": "XRP-USD",
    "cardano": "ADA-USD",
    "dogecoin": "DOGE-USD",
    "avalanche-2": "AVAX-USD",
    "shiba-inu": "SHIB-USD",
    "polkadot": "DOT-USD",
    "chainlink": "LINK-USD",
    "polygon-ecosystem-token": "POL-USD",
    "near": "NEAR-USD",
    "litecoin": "LTC-USD",
    "uniswap": "UNI-USD",
    "render-token": "RENDER-USD",
    "sui": "SUI-USD",
    "aptos": "APT-USD",
    "pepe": "PEPE-USD",
    "fetch-ai": "FET-USD"
}

# Default Top Coins Fallback Data in case external API fails or rate limits
FALLBACK_COINS = [
    {
        "id": "bitcoin", "symbol": "btc", "name": "Bitcoin", "current_price": 96450.0,
        "price_change_percentage_24h": 2.45, "total_volume": 38400000000, "market_cap": 1905000000000,
        "market_cap_rank": 1, "high_24h": 97800.0, "low_24h": 94200.0,
        "image": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png"
    },
    {
        "id": "ethereum", "symbol": "eth", "name": "Ethereum", "current_price": 2780.0,
        "price_change_percentage_24h": 3.12, "total_volume": 18200000000, "market_cap": 334000000000,
        "market_cap_rank": 2, "high_24h": 2840.0, "low_24h": 2690.0,
        "image": "https://assets.coingecko.com/coins/images/279/large/ethereum.png"
    },
    {
        "id": "solana", "symbol": "sol", "name": "Solana", "current_price": 194.50,
        "price_change_percentage_24h": 6.84, "total_volume": 6500000000, "market_cap": 91000000000,
        "market_cap_rank": 3, "high_24h": 198.0, "low_24h": 181.2,
        "image": "https://assets.coingecko.com/coins/images/4128/large/solana.png"
    },
    {
        "id": "binancecoin", "symbol": "bnb", "name": "BNB", "current_price": 645.0,
        "price_change_percentage_24h": 1.15, "total_volume": 1200000000, "market_cap": 94000000000,
        "market_cap_rank": 4, "high_24h": 652.0, "low_24h": 638.0,
        "image": "https://assets.coingecko.com/coins/images/825/large/bnb-icon2_2x.png"
    },
    {
        "id": "ripple", "symbol": "xrp", "name": "XRP", "current_price": 2.38,
        "price_change_percentage_24h": 4.50, "total_volume": 4900000000, "market_cap": 136000000000,
        "market_cap_rank": 5, "high_24h": 2.46, "low_24h": 2.25,
        "image": "https://assets.coingecko.com/coins/images/44/large/xrp-symbol-white-128.png"
    },
    {
        "id": "cardano", "symbol": "ada", "name": "Cardano", "current_price": 0.78,
        "price_change_percentage_24h": -0.85, "total_volume": 850000000, "market_cap": 27500000000,
        "market_cap_rank": 6, "high_24h": 0.82, "low_24h": 0.76,
        "image": "https://assets.coingecko.com/coins/images/975/large/cardano.png"
    },
    {
        "id": "dogecoin", "symbol": "doge", "name": "Dogecoin", "current_price": 0.265,
        "price_change_percentage_24h": 5.40, "total_volume": 2400000000, "market_cap": 38800000000,
        "market_cap_rank": 7, "high_24h": 0.28, "low_24h": 0.25,
        "image": "https://assets.coingecko.com/coins/images/5/large/dogecoin.png"
    },
    {
        "id": "avalanche-2", "symbol": "avax", "name": "Avalanche", "current_price": 32.40,
        "price_change_percentage_24h": 3.75, "total_volume": 580000000, "market_cap": 13200000000,
        "market_cap_rank": 8, "high_24h": 33.5, "low_24h": 31.0,
        "image": "https://assets.coingecko.com/coins/images/12559/large/Avalanche_Circle_RedWhite_Trans.png"
    },
    {
        "id": "chainlink", "symbol": "link", "name": "Chainlink", "current_price": 18.20,
        "price_change_percentage_24h": 2.10, "total_volume": 420000000, "market_cap": 11000000000,
        "market_cap_rank": 9, "high_24h": 18.8, "low_24h": 17.6,
        "image": "https://assets.coingecko.com/coins/images/877/large/chainlink-new-logo.png"
    },
    {
        "id": "sui", "symbol": "sui", "name": "Sui", "current_price": 3.42,
        "price_change_percentage_24h": 8.90, "total_volume": 1450000000, "market_cap": 9800000000,
        "market_cap_rank": 10, "high_24h": 3.55, "low_24h": 3.12,
        "image": "https://assets.coingecko.com/coins/images/26375/large/sui-ocean-square.png"
    }
]

async def fetch_coingecko_markets(currency: str = "usd", limit: int = 100):
    cache_key = f"markets_{currency}_{limit}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency={currency}&order=market_cap_desc&per_page={limit}&page=1&sparkline=true&price_change_percentage=24h,7d"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            res = await client.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and len(data) > 0:
                    set_cached(cache_key, data, ttl=60)
                    return data
    except Exception as e:
        print("CoinGecko API fetch warning:", e)

    # If CoinGecko is busy/rate-limited, return converted fallback data
    rate = CURRENCY_RATES.get(currency.lower(), 1.0)
    adjusted_fallback = []
    for coin in FALLBACK_COINS:
        c = coin.copy()
        c["current_price"] = round(c["current_price"] * rate, 2)
        c["high_24h"] = round(c["high_24h"] * rate, 2)
        c["low_24h"] = round(c["low_24h"] * rate, 2)
        c["market_cap"] = round(c["market_cap"] * rate, 2)
        c["total_volume"] = round(c["total_volume"] * rate, 2)
        adjusted_fallback.append(c)
    return adjusted_fallback

@router.get("/coins")
async def get_coins(currency: str = Query("usd", pattern="^(usd|inr|eur|gbp)$"), limit: int = Query(50, ge=1, le=250)):
    return await fetch_coingecko_markets(currency=currency, limit=limit)

@router.get("/coins/{coin_id}")
async def get_coin_details(coin_id: str, currency: str = "usd"):
    cache_key = f"coin_details_{coin_id}_{currency}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=true&developer_data=false&sparkline=true"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            res = await client.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                set_cached(cache_key, data, ttl=90)
                return data
    except Exception as e:
        print(f"Error fetching coin details for {coin_id}:", e)

    # Fallback from markets
    markets = await fetch_coingecko_markets(currency=currency, limit=100)
    for c in markets:
        if c.get("id") == coin_id or c.get("symbol") == coin_id.lower():
            return {
                "id": c["id"],
                "symbol": c["symbol"],
                "name": c["name"],
                "image": {"large": c.get("image")},
                "description": {"en": f"{c['name']} is one of the leading cryptocurrencies globally by market capitalization."},
                "market_data": {
                    "current_price": {currency: c.get("current_price")},
                    "market_cap": {currency: c.get("market_cap")},
                    "total_volume": {currency: c.get("total_volume")},
                    "high_24h": {currency: c.get("high_24h")},
                    "low_24h": {currency: c.get("low_24h")},
                    "price_change_percentage_24h": c.get("price_change_percentage_24h"),
                    "circulating_supply": c.get("circulating_supply", 0),
                    "total_supply": c.get("total_supply", 0)
                }
            }

    raise HTTPException(status_code=404, detail="Cryptocurrency not found")

@router.get("/coins/{coin_id}/historical")
async def get_coin_historical(coin_id: str, days: str = Query("30"), currency: str = "usd"):
    cache_key = f"hist_{coin_id}_{days}_{currency}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency={currency}&days={days}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            res = await client.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                set_cached(cache_key, data, ttl=60)
                return data
    except Exception as e:
        print(f"CoinGecko history error for {coin_id}:", e)

    # Fallback to Yahoo Finance using yfinance
    ticker_symbol = COIN_TICKER_MAP.get(coin_id.lower(), f"{coin_id.upper()}-USD")
    period_map = {"1": "1d", "7": "7d", "14": "14d", "30": "1mo", "90": "3mo", "365": "1y", "max": "max"}
    interval_map = {"1": "15m", "7": "1h", "14": "1h", "30": "1d", "90": "1d", "365": "1d", "max": "1wk"}

    period = period_map.get(str(days), "1mo")
    interval = interval_map.get(str(days), "1d")

    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period=period, interval=interval)
        if not df.empty:
            rate = CURRENCY_RATES.get(currency.lower(), 1.0)
            prices = []
            market_caps = []
            total_volumes = []
            
            for index, row in df.iterrows():
                ts = int(index.timestamp() * 1000)
                price = float(row["Close"]) * rate
                volume = float(row["Volume"]) * rate
                prices.append([ts, price])
                market_caps.append([ts, price * 19000000]) # approximate
                total_volumes.append([ts, volume])
            
            result = {
                "prices": prices,
                "market_caps": market_caps,
                "total_volumes": total_volumes
            }
            set_cached(cache_key, result, ttl=60)
            return result
    except Exception as err:
        print(f"yfinance fallback failed for {ticker_symbol}:", err)

    raise HTTPException(status_code=500, detail="Failed to fetch historical market data")

@router.get("/fear-and-greed")
async def get_fear_greed():
    cached = get_cached("fear_greed")
    if cached:
        return cached

    url = "https://api.alternative.me/fng/?limit=1"
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            res = await client.get(url)
            if res.status_code == 200:
                data = res.json()
                if "data" in data and len(data["data"]) > 0:
                    result = data["data"][0]
                    set_cached("fear_greed", result, ttl=300)
                    return result
    except Exception:
        pass

    return {
        "value": "72",
        "value_classification": "Greed",
        "timestamp": str(int(time.time()))
    }

@router.get("/global")
async def get_global_stats():
    cached = get_cached("global_stats")
    if cached:
        return cached

    url = "https://api.coingecko.com/api/v3/global"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(url)
            if res.status_code == 200:
                data = res.json().get("data", {})
                set_cached("global_stats", data, ttl=120)
                return data
    except Exception:
        pass

    return {
        "active_cryptocurrencies": 14280,
        "total_market_cap": {"usd": 3250000000000, "inr": 282100000000000},
        "total_volume": {"usd": 128400000000, "inr": 11145000000000},
        "market_cap_percentage": {"btc": 58.4, "eth": 12.8, "sol": 4.1},
        "market_cap_change_percentage_24h_usd": 2.15
    }
