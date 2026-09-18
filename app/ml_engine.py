import numpy as np
import pandas as pd
import yfinance as yf
from math import sqrt
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor, GradientBoostingRegressor
try:
    from xgboost import XGBRegressor
    HAS_XGBOOST = True
except Exception:
    HAS_XGBOOST = False

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/predict", tags=["AI & Machine Learning"])

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

def compute_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def generate_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    
    # Lags
    for col in ['Open', 'Close', 'High', 'Low', 'Volume']:
        data[f'{col}_lag1'] = data[col].shift(1)
        data[f'{col}_lag2'] = data[col].shift(2)
        data[f'{col}_lag3'] = data[col].shift(3)
    
    # Moving averages
    data['SMA_7'] = data['Close'].rolling(window=7).mean()
    data['SMA_20'] = data['Close'].rolling(window=20).mean()
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    data['EMA_12'] = data['Close'].ewm(span=12, adjust=False).mean()
    data['EMA_26'] = data['Close'].ewm(span=26, adjust=False).mean()
    
    # Volatility & Bollinger Bands
    data['Std_20'] = data['Close'].rolling(window=20).std()
    data['BB_Upper'] = data['SMA_20'] + (2 * data['Std_20'])
    data['BB_Lower'] = data['SMA_20'] - (2 * data['Std_20'])
    data['BB_Width'] = (data['BB_Upper'] - data['BB_Lower']) / (data['SMA_20'] + 1e-9)
    
    # RSI & MACD
    data['RSI_14'] = compute_rsi(data['Close'], 14)
    macd, signal, hist = compute_macd(data['Close'])
    data['MACD'] = macd
    data['MACD_Signal'] = signal
    data['MACD_Hist'] = hist

    # Daily Return and Price Range
    data['Daily_Return'] = data['Close'].pct_change()
    data['Price_Range'] = (data['High'] - data['Low']) / (data['Close'] + 1e-9)

    return data.dropna()

def train_and_predict(symbol: str, days_ahead: int = 7):
    # Ensure proper ticker format
    ticker_symbol = symbol.strip().upper()
    if not ticker_symbol.endswith("-USD") and not ticker_symbol.endswith("USD"):
        ticker_symbol = f"{ticker_symbol}-USD"

    # Download data (2 years for solid training)
    ticker = yf.Ticker(ticker_symbol)
    history = ticker.history(period="2y", interval="1d")
    
    if history.empty or len(history) < 60:
        # Retry with 1y or basic symbol
        history = ticker.history(period="1y", interval="1d")
        if history.empty or len(history) < 30:
            raise HTTPException(status_code=400, detail=f"Insufficient historical data found for {ticker_symbol}")

    current_price = float(history['Close'].iloc[-1])
    recent_high = float(history['High'].tail(30).max())
    recent_low = float(history['Low'].tail(30).min())
    
    # Feature engineering
    feature_df = generate_technical_features(history)
    if len(feature_df) < 30:
        raise HTTPException(status_code=400, detail="Data after indicator computation was too short")

    feature_cols = [
        'Open_lag1', 'Close_lag1', 'High_lag1', 'Low_lag1', 'Volume_lag1',
        'Open_lag2', 'Close_lag2', 'High_lag2', 'Low_lag2',
        'Open_lag3', 'Close_lag3', 'High_lag3', 'Low_lag3',
        'SMA_7', 'SMA_20', 'SMA_50', 'EMA_12', 'EMA_26',
        'BB_Upper', 'BB_Lower', 'BB_Width', 'RSI_14', 'MACD', 'MACD_Signal', 'MACD_Hist',
        'Daily_Return', 'Price_Range'
    ]

    target_cols = ['Open', 'High', 'Low', 'Close']
    
    X = feature_df[feature_cols].values
    latest_feature_vector = feature_df[feature_cols].iloc[-1].values.reshape(1, -1)

    predictions = {}
    rmse_metrics = {}
    r2_scores = {}
    
    for target in target_cols:
        y = feature_df[target].values
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, shuffle=False)
        
        if HAS_XGBOOST:
            try:
                model = XGBRegressor(n_estimators=100, learning_rate=0.08, max_depth=4, random_state=42)
                model.fit(X_train, y_train)
            except Exception:
                model = HistGradientBoostingRegressor(max_iter=100, learning_rate=0.08, max_depth=5, random_state=42)
                model.fit(X_train, y_train)
        else:
            model = HistGradientBoostingRegressor(max_iter=100, learning_rate=0.08, max_depth=5, random_state=42)
            model.fit(X_train, y_train)

        test_preds = model.predict(X_test)
        rmse = float(sqrt(mean_squared_error(y_test, test_preds)))
        r2 = float(r2_score(y_test, test_preds))
        
        next_val = float(model.predict(latest_feature_vector)[0])
        predictions[target] = round(next_val, 2 if next_val > 10 else 4)
        rmse_metrics[f"RMSE_{target}"] = round(rmse, 2 if rmse > 10 else 4)
        r2_scores[f"R2_{target}"] = round(max(0.0, r2) * 100, 2)

    predicted_next_close = predictions['Close']
    pct_change = round(((predicted_next_close - current_price) / current_price) * 100, 2)
    
    # Generate multi-day projection trajectory (1d, 3d, 7d, 14d, 30d)
    latest_rsi = float(feature_df['RSI_14'].iloc[-1])
    latest_macd = float(feature_df['MACD'].iloc[-1])
    latest_signal = float(feature_df['MACD_Signal'].iloc[-1])
    latest_sma20 = float(feature_df['SMA_20'].iloc[-1])
    latest_sma50 = float(feature_df['SMA_50'].iloc[-1])

    # Multi-day forecasting trajectory
    forecast_trajectory = []
    base_price = current_price
    daily_drift = (predicted_next_close - current_price)
    
    for day in range(1, days_ahead + 1):
        # Dampen trend curve with slight realistic mean-reverting decay
        decay = 1.0 / (1.0 + (day * 0.04))
        projected = base_price + (daily_drift * day * decay)
        # Add slight volatility bounds
        volatility_band = projected * (0.015 * sqrt(day))
        forecast_trajectory.append({
            "day": day,
            "projected_price": round(projected, 2 if projected > 10 else 4),
            "upper_bound": round(projected + volatility_band, 2 if projected > 10 else 4),
            "lower_bound": round(max(0.01, projected - volatility_band), 2 if projected > 10 else 4)
        })

    # AI Trading Signal Generation
    score = 0
    reasons = []

    # 1. Price projection score
    if pct_change > 3.0:
        score += 2
        reasons.append(f"ML Model forecasts a strong +{pct_change}% upward price movement.")
    elif pct_change > 0.5:
        score += 1
        reasons.append(f"ML Model projects a moderate +{pct_change}% gain.")
    elif pct_change < -3.0:
        score -= 2
        reasons.append(f"ML Model forecasts a significant -{abs(pct_change)}% downward pullback.")
    elif pct_change < -0.5:
        score -= 1
        reasons.append(f"ML Model projects a slight -{abs(pct_change)}% decline.")
    else:
        reasons.append("ML Model predicts price consolidation within ±0.5% range.")

    # 2. RSI Indicator
    if latest_rsi < 32:
        score += 2
        reasons.append(f"RSI is {latest_rsi:.1f} (Oversold condition — strong rebound potential).")
    elif latest_rsi > 68:
        score -= 2
        reasons.append(f"RSI is {latest_rsi:.1f} (Overbought condition — pullback risk).")
    else:
        reasons.append(f"RSI is {latest_rsi:.1f} (Neutral momentum).")

    # 3. MACD Momentum
    if latest_macd > latest_signal:
        score += 1
        reasons.append("MACD is above the Signal Line (Bullish momentum crossover).")
    else:
        score -= 1
        reasons.append("MACD is below the Signal Line (Bearish momentum pressure).")

    # 4. Moving Average Trend
    if current_price > latest_sma50:
        score += 1
        reasons.append("Price is trading above the 50-day Simple Moving Average (Uptrend).")
    else:
        score -= 1
        reasons.append("Price is trading below the 50-day Simple Moving Average (Downtrend).")

    # Determine Final Signal
    if score >= 3:
        signal_badge = "STRONG BUY"
        signal_color = "emerald"
    elif score in [1, 2]:
        signal_badge = "BUY"
        signal_color = "green"
    elif score == 0:
        signal_badge = "HOLD / NEUTRAL"
        signal_color = "amber"
    elif score in [-1, -2]:
        signal_badge = "SELL"
        signal_color = "orange"
    else:
        signal_badge = "STRONG SELL"
        signal_color = "rose"

    # Support & Resistance Calculation
    support_1 = round(current_price * 0.965, 2 if current_price > 10 else 4)
    support_2 = round(recent_low * 0.99, 2 if current_price > 10 else 4)
    resistance_1 = round(current_price * 1.042, 2 if current_price > 10 else 4)
    resistance_2 = round(recent_high * 1.01, 2 if current_price > 10 else 4)

    return {
        "symbol": ticker_symbol,
        "current_price": round(current_price, 2 if current_price > 10 else 4),
        "predicted_next_day": {
            "open": predictions['Open'],
            "high": predictions['High'],
            "low": predictions['Low'],
            "close": predictions['Close'],
            "expected_change_pct": pct_change
        },
        "model_metrics": {
            **rmse_metrics,
            **r2_scores,
            "average_confidence_pct": round(np.mean(list(r2_scores.values())), 1)
        },
        "technical_indicators": {
            "rsi": round(latest_rsi, 2),
            "macd": round(latest_macd, 2),
            "macd_signal": round(latest_signal, 2),
            "sma_20": round(latest_sma20, 2),
            "sma_50": round(latest_sma50, 2),
            "support_level_1": support_1,
            "support_level_2": support_2,
            "resistance_level_1": resistance_1,
            "resistance_level_2": resistance_2
        },
        "ai_analysis": {
            "signal": signal_badge,
            "signal_color": signal_color,
            "score": score,
            "reasons": reasons
        },
        "forecast_trajectory": forecast_trajectory
    }

@router.get("/")
def run_prediction(symbol: str = Query("BTC-USD", description="Ticker symbol like BTC-USD, ETH-USD, SOL-USD"), days: int = Query(7, ge=1, le=30)):
    try:
        return train_and_predict(symbol=symbol, days_ahead=days)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction algorithm error: {str(e)}")
