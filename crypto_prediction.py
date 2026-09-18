"""
CryptoPulse AI — Standalone ML Cryptocurrency Prediction Script
Can be run as a CLI or with Streamlit
"""
import yfinance as yf
import numpy as np
import pandas as pd
from math import sqrt
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

def predict_crypto_prices(crypto_name="BTC-USD"):
    if not crypto_name.endswith("-USD"):
        crypto_name = f"{crypto_name}-USD"

    print(f"Downloading historical data for {crypto_name}...")
    data = yf.download(crypto_name, period="1y", interval="1d", progress=False)
    if data.empty:
        raise ValueError(f"No market data found for {crypto_name}")

    # Handle multi-index columns if yfinance returns them
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # Feature engineering
    data['Previous_Open'] = data['Open'].shift(1)
    data['Previous_Close'] = data['Close'].shift(1)
    data['Previous_Low'] = data['Low'].shift(1)
    data['Previous_High'] = data['High'].shift(1)
    data['SMA_20'] = data['Close'].rolling(window=20).mean()
    data['RSI_14'] = compute_rsi(data['Close'], 14)
    data = data.dropna()

    features = ['Previous_Open', 'Previous_Close', 'Previous_Low', 'Previous_High', 'SMA_20', 'RSI_14']
    targets = ['Open', 'Close', 'Low', 'High']

    results = {}
    rmse_results = {}

    X = data[features].values
    latest_features = data[features].iloc[-1].values.reshape(1, -1)

    for target in targets:
        y = data[target].values
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, shuffle=False)
        
        model = HistGradientBoostingRegressor(max_iter=100, learning_rate=0.08, max_depth=5, random_state=42)
        model.fit(X_train, y_train)

        test_preds = model.predict(X_test)
        rmse = sqrt(mean_squared_error(y_test, test_preds))
        pred_val = float(model.predict(latest_features)[0])

        results[target] = round(pred_val, 2)
        rmse_results[f"RMSE_{target}"] = round(rmse, 2)

    current_close = float(data['Close'].iloc[-1])
    results['Current_Price'] = round(current_close, 2)
    results['Expected_Change_%'] = round(((results['Close'] - current_close) / current_close) * 100, 2)
    
    return pd.DataFrame([results]), pd.DataFrame([rmse_results])

if __name__ == "__main__":
    import sys
    symbol = sys.argv[1] if len(sys.argv) > 1 else "BTC-USD"
    preds_df, rmse_df = predict_crypto_prices(symbol)
    print("\n--- PREDICTED PRICES ---")
    print(preds_df.to_string(index=False))
    print("\n--- RMSE ACCURACY METRICS ---")
    print(rmse_df.to_string(index=False))
