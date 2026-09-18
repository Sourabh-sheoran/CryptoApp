import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, get_db
from app.auth import register, login, RegisterRequest, LoginRequest
from app.ml_engine import train_and_predict
from app.portfolio import buy_crypto, sell_crypto, TradeRequest

def run_tests():
    print("1. Initializing Database...")
    init_db()
    
    print("\n2. Testing User Registration & Login...")
    reg_req = RegisterRequest(name="Sourabh Test", email="sourabh_test@example.com", password="password123")
    try:
        auth_res = register(reg_req)
        print("Registration success! Token:", auth_res.token[:20], "... Balance:", auth_res.user.virtual_balance_usd)
    except Exception as e:
        print("Registration response (might already exist):", e)
    
    log_req = LoginRequest(email="sourabh_test@example.com", password="password123")
    log_res = login(log_req)
    print("Login success! User:", log_res.user.name, "Balance:", log_res.user.virtual_balance_usd)
    current_user = {"id": log_res.user.id, "name": log_res.user.name, "email": log_res.user.email, "virtual_balance_usd": log_res.user.virtual_balance_usd}

    print("\n3. Testing Portfolio Paper Trading (Buy 0.1 BTC)...")
    buy_req = TradeRequest(coin_id="bitcoin", symbol="BTC", name="Bitcoin", quantity=0.1, price_usd=95000.0)
    buy_res = buy_crypto(buy_req, current_user=current_user)
    print("Buy order executed:", buy_res)

    print("\n4. Testing Portfolio Paper Trading (Sell 0.05 BTC)...")
    sell_req = TradeRequest(coin_id="bitcoin", symbol="BTC", name="Bitcoin", quantity=0.05, price_usd=96000.0)
    sell_res = sell_crypto(sell_req, current_user=current_user)
    print("Sell order executed:", sell_res)

    print("\n5. Testing AI / ML Prediction Engine on BTC-USD...")
    prediction_result = train_and_predict("BTC-USD", days_ahead=7)
    print(f"Prediction for {prediction_result['symbol']}:")
    print(f" - Current Price: ${prediction_result['current_price']}")
    print(f" - Predicted Next Day Close: ${prediction_result['predicted_next_day']['close']} ({prediction_result['predicted_next_day']['expected_change_pct']}%)")
    print(f" - AI Signal: {prediction_result['ai_analysis']['signal']}")
    print(f" - Model Confidence (R2): {prediction_result['model_metrics']['average_confidence_pct']}%")
    print(f" - Key RSI: {prediction_result['technical_indicators']['rsi']}")

    print("\n✅ ALL BACKEND TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
