import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)

PDF_FILENAME = "CryptoPulse_AI_Complete_Project_Documentation.pdf"

def generate_pdf():
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), PDF_FILENAME)
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1e1b4b'),
        alignment=1, # Center
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#4338ca'),
        alignment=1,
        spaceAfter=20
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=16,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#334155'),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#374151'),
        leftIndent=15,
        spaceAfter=3
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#0f172a'),
        backColor=colors.HexColor('#f1f5f9'),
        spaceBefore=4,
        spaceAfter=6
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#1e40af'),
        backColor=colors.HexColor('#eff6ff'),
        borderColor=colors.HexColor('#bfdbfe'),
        borderWidth=1,
        borderPadding=8,
        spaceBefore=6,
        spaceAfter=8
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("CryptoPulse AI — Complete Project Documentation & Master Guide", title_style))
    story.append(Paragraph("Full-Stack AI-Powered Cryptocurrency Tracking, Machine Learning Price Forecasting & Paper Trading Platform", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#6366f1'), spaceAfter=14))

    # Metadata Table
    meta_data = [
        [Paragraph("<b>Project Name:</b> CryptoPulse AI", body_style), Paragraph("<b>Architecture:</b> Pure Python Full-Stack (FastAPI + SQLite + ML)", body_style)],
        [Paragraph("<b>Author / Developer:</b> Sourabh Sheoran", body_style), Paragraph("<b>Live Server Port:</b> http://localhost:8000", body_style)],
        [Paragraph("<b>Core ML Models:</b> HistGradientBoosting, Random Forest", body_style), Paragraph("<b>Repository:</b> github.com/Sourabh-sheoran/CryptoApp", body_style)]
    ]
    t = Table(meta_data, colWidths=[260, 270])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    # Section 1: Executive Summary
    story.append(Paragraph("1. Executive Summary & Core Purpose", h1_style))
    story.append(Paragraph("CryptoPulse AI is a production-grade, full-stack cryptocurrency market analytics and algorithmic forecasting platform developed completely in Python. The platform addresses the volatility and complexity of the digital asset markets by providing traders and investors with three fundamental pillars:", body_style))
    story.append(Paragraph("• <b>Real-Time Market Ingestion:</b> High-frequency live price streaming for top 100+ cryptocurrencies, global market metrics (Total Market Cap, 24h Volume, BTC Dominance), and the Alternative.me Fear & Greed Sentiment Index.", bullet_style))
    story.append(Paragraph("• <b>Machine Learning Price Prediction Engine:</b> Automated feature engineering over historical OHLCV data that calculates 27+ statistical/technical indicators (RSI, MACD, Bollinger Bands, Moving Averages) to train Gradient Boosted Regressors predicting next-day Open, High, Low, Close prices with multi-day trajectory forecasting and automated Buy/Sell/Hold signals.", bullet_style))
    story.append(Paragraph("• <b>Paper Trading Simulator:</b> Zero-risk virtual portfolio execution with $50,000.00 USD initial simulated capital, atomic database transactions, real-time P&L tracking, weighted average cost accounting, and watchlist persistence.", bullet_style))

    story.append(Spacer(1, 10))

    # Section 2: Complete Tech Stack
    story.append(Paragraph("2. Complete Technology Stack & Specifications", h1_style))
    tech_data = [
        ["Layer / Category", "Technologies & Libraries", "Purpose & Architectural Rationale"],
        ["Backend Framework", "FastAPI, Uvicorn, ASGI", "High-performance asynchronous Python REST framework with automatic OpenAPI/Swagger docs and async I/O."],
        ["Database", "SQLite 3, Thread-Safe Context", "Embedded, zero-configuration relational database with foreign key cascades and atomic ACID transactions."],
        ["Security & Auth", "Bcrypt, Python-Jose (JWT)", "Salted password hashing preventing rainbow attacks, stateless HMAC-SHA256 bearer tokens with 7-day expiration."],
        ["Machine Learning", "Scikit-Learn, NumPy, Pandas", "HistGradientBoostingRegressor & RandomForest ensembles, TimeSeries split, RMSE / R² evaluation metrics."],
        ["Financial Data", "yfinance, Httpx, CoinGecko REST", "2-year daily historical OHLCV data ingestion, live market tickers, and in-memory TTL caching (45s)."],
        ["Frontend UI", "HTML5, Vanilla JS, CSS3, Chart.js", "Cyberpunk dark glassmorphism dashboard, dynamic canvas charting with confidence bands, and responsive modals."]
    ]
    tech_table = Table(
        [[Paragraph(f"<b>{cell}</b>" if i==0 else cell, body_style) for cell in row] for i, row in enumerate(tech_data)],
        colWidths=[110, 160, 260]
    )
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e0e7ff')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#94a3b8')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(tech_table)

    story.append(Spacer(1, 14))

    # Section 3: Machine Learning Engine Deep Dive
    story.append(Paragraph("3. Machine Learning Engine & Mathematical Foundations", h1_style))
    story.append(Paragraph("The Machine Learning subsystem in <code>app/ml_engine.py</code> is engineered to perform multi-target regression on sequential financial data without lookahead bias:", body_style))
    
    story.append(Paragraph("A. Mathematical Formulations of Extracted Features:", h2_style))
    story.append(Paragraph("1. <b>Relative Strength Index (RSI - 14 Periods):</b> Measures directional price momentum on a 0-100 scale:<br/>"
                           "&nbsp;&nbsp;&nbsp;&nbsp;<i>RS = (Avg Gain over 14d) / (Avg Loss over 14d)</i><br/>"
                           "&nbsp;&nbsp;&nbsp;&nbsp;<i>RSI = 100 - (100 / (1 + RS))</i><br/>"
                           "&nbsp;&nbsp;&nbsp;&nbsp;Interpretation: RSI &lt; 30 indicates oversold conditions (bullish reversal); RSI &gt; 70 indicates overbought conditions (bearish pullback).", body_style))
    
    story.append(Paragraph("2. <b>Moving Average Convergence Divergence (MACD):</b> Captures trend velocity and crossovers:<br/>"
                           "&nbsp;&nbsp;&nbsp;&nbsp;<i>MACD Line = EMA(12) - EMA(26)</i><br/>"
                           "&nbsp;&nbsp;&nbsp;&nbsp;<i>Signal Line = EMA(9, MACD Line)</i><br/>"
                           "&nbsp;&nbsp;&nbsp;&nbsp;<i>Histogram = MACD Line - Signal Line</i><br/>"
                           "&nbsp;&nbsp;&nbsp;&nbsp;Interpretation: MACD crossing above Signal line generates a bullish momentum trigger.", body_style))

    story.append(Paragraph("3. <b>Bollinger Bands (20 Periods, 2 Std Deviations):</b> Measures dynamic price envelope and volatility:<br/>"
                           "&nbsp;&nbsp;&nbsp;&nbsp;<i>Upper Band = SMA(20) + 2 * σ(20)</i><br/>"
                           "&nbsp;&nbsp;&nbsp;&nbsp;<i>Lower Band = SMA(20) - 2 * σ(20)</i><br/>"
                           "&nbsp;&nbsp;&nbsp;&nbsp;<i>Band Width = (Upper Band - Lower Band) / SMA(20)</i>", body_style))

    story.append(Paragraph("4. <b>Autoregressive Lags & Price Range:</b> Previous 1-day, 2-day, and 3-day Open, High, Low, Close, Volume lags, and Normalized Daily Range <i>(High - Low) / Close</i>.", body_style))

    story.append(Paragraph("B. Model Training & Trajectory Forecasting Architecture:", h2_style))
    story.append(Paragraph("• <b>Algorithm:</b> <code>HistGradientBoostingRegressor</code> (Histogram-based decision trees with early stopping and L2 regularization) trained independently for 4 targets: <i>Open, High, Low, Close</i>.<br/>"
                           "• <b>Train/Test Protocol:</b> 85/15 sequential time-series split (<code>shuffle=False</code>) ensuring zero historical data leakage.<br/>"
                           "• <b>Multi-day Forecast Trajectory:</b> Projects day 1 to day 30 forward with a mean-reverting drift decay factor <i>decay = 1 / (1 + day * 0.04)</i> and a volatility expansion band <i>± Price * (0.015 * sqrt(day))</i> providing upper and lower 95% confidence intervals.<br/>"
                           "• <b>Evaluation Metrics:</b> Root Mean Squared Error (RMSE) and R² Coefficient of Determination.", body_style))

    story.append(Spacer(1, 10))

    # Section 4: Database Schema & Architecture
    story.append(Paragraph("4. Relational Database Schema & Data Models", h1_style))
    story.append(Paragraph("The system utilizes an embedded SQLite database (<code>cryptoapp.db</code>) with strict schema normalization and foreign key constraints:", body_style))

    db_data = [
        ["Table Name", "Primary Columns & Types", "Key Relationships & Constraints"],
        ["users", "id (INTEGER PK), name (TEXT), email (TEXT UNIQUE), password_hash (TEXT), virtual_balance_usd (REAL DEFAULT 50000.0), created_at", "Parent entity for Portfolios, Transactions, and Watchlists."],
        ["portfolios", "id (PK), user_id (FK), coin_id (TEXT), symbol (TEXT), name (TEXT), quantity (REAL), avg_buy_price_usd (REAL), total_invested_usd (REAL)", "UNIQUE(user_id, coin_id). Automatically tracks weighted-average cost basis."],
        ["transactions", "id (PK), user_id (FK), type ('BUY'|'SELL'), coin_id (TEXT), symbol (TEXT), quantity (REAL), price_usd (REAL), total_usd (REAL), timestamp", "Complete immutable trade ledger and execution history."],
        ["watchlists", "id (PK), user_id (FK), coin_id (TEXT), symbol (TEXT), name (TEXT), added_at", "UNIQUE(user_id, coin_id). Stores user starred assets."]
    ]
    db_table = Table(
        [[Paragraph(f"<b>{cell}</b>" if i==0 else cell, body_style) for cell in row] for i, row in enumerate(db_data)],
        colWidths=[80, 220, 230]
    )
    db_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e0e7ff')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#94a3b8')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(db_table)

    story.append(PageBreak())

    # Section 5: API Endpoints
    story.append(Paragraph("5. Complete REST API Specifications", h1_style))
    api_data = [
        ["Method & Route", "Description", "Auth Required?", "Key Parameters / Request Body"],
        ["POST /api/auth/register", "Register a new user account with $50k virtual balance", "No", "{ name, email, password }"],
        ["POST /api/auth/login", "Authenticate user credentials & issue JWT token", "No", "{ email, password }"],
        ["GET /api/auth/me", "Retrieve current authenticated user profile & balance", "Yes (Bearer)", "None"],
        ["POST /api/auth/reset-balance", "Reset paper trading portfolio & restore $50k funds", "Yes (Bearer)", "None"],
        ["GET /api/market/coins", "Stream top 100 cryptocurrencies with sparklines", "No", "currency (usd/inr/eur), limit"],
        ["GET /api/market/coins/{id}", "Get in-depth asset stats, circulating supply, ATH", "No", "id (e.g. bitcoin), currency"],
        ["GET /api/market/coins/{id}/historical", "Historical price & volume timeseries for Chart.js", "No", "id, days (1, 7, 30, 90, 365), currency"],
        ["GET /api/market/fear-and-greed", "Live Alternative.me Fear & Greed sentiment index", "No", "None"],
        ["GET /api/predict/", "Execute ML price forecast & AI trade signals", "No", "symbol (e.g. BTC-USD), days (1-30)"],
        ["GET /api/portfolio/", "Get user net worth, holdings, live P&L, trade ledger", "Yes (Bearer)", "None"],
        ["POST /api/portfolio/buy", "Execute simulated Buy order at live market price", "Yes (Bearer)", "{ coin_id, symbol, name, quantity, price_usd }"],
        ["POST /api/portfolio/sell", "Execute simulated Sell order at live market price", "Yes (Bearer)", "{ coin_id, symbol, name, quantity, price_usd }"],
        ["GET/POST/DELETE /api/portfolio/watchlist", "View, add, or remove assets from user watchlist", "Yes (Bearer)", "{ coin_id, symbol, name }"]
    ]
    api_table = Table(
        [[Paragraph(f"<b>{cell}</b>" if i==0 else cell, body_style) for cell in row] for i, row in enumerate(api_data)],
        colWidths=[140, 180, 75, 135]
    )
    api_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e0e7ff')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#94a3b8')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(api_table)

    story.append(Spacer(1, 14))

    # Section 6: Interview Preparation & Ready Answers
    story.append(Paragraph("6. Interview Master Cheat Sheet & Ready Responses", h1_style))
    
    story.append(Paragraph("<b>Ready-to-Speak 60-Second Elevator Pitch (English):</b>", h2_style))
    story.append(Paragraph(
        "\"I have developed CryptoPulse AI, a full-stack, AI-driven cryptocurrency market analytics and machine learning price forecasting platform built entirely in Python using FastAPI. "
        "On the backend, I implemented an embedded SQLite database secured with Bcrypt password hashing and JWT authentication, providing every user with $50,000 USD in virtual capital for real-time paper trading with live P&L tracking. "
        "The core highlight of the project is its Machine Learning Engine, which fetches historical market data via yfinance and engineers over 27 statistical features including 14-period RSI, MACD, Moving Averages (SMA 20/50), and Bollinger Bands. "
        "Using HistGradientBoosting Regressors, the system forecasts future Open, High, Low, and Close prices with confidence interval trajectories and generates automated AI Trading Signals (Buy, Sell, Hold). "
        "The frontend is a dark cyberpunk glassmorphism terminal built with Chart.js and Vanilla JS that delivers real-time market data, multi-currency conversion, and Fear & Greed sentiment index.\"",
        callout_style
    ))

    story.append(Paragraph("<b>Ready-to-Speak 60-Second Elevator Pitch (Hinglish):</b>", h2_style))
    story.append(Paragraph(
        "\"Maine CryptoPulse AI develop kiya hai — jo ek Full-Stack AI-Powered Cryptocurrency Tracking, Machine Learning Price Prediction aur Paper Trading Platform hai. "
        "Is project ko maine purely Python aur FastAPI par build kiya hai. Backend me maine SQLite database ke sath secure Bcrypt password hashing aur JWT token authentication implement kiya hai, jisme har user ko $50,000 USD virtual capital milta hai real-time simulated trading ke liye. "
        "Iska sabse important component iska Machine Learning Engine hai, jisme hum yfinance se historical OHLCV data fetch karke 27+ statistical features (jaise 14-period RSI, MACD momentum, Bollinger Bands, aur 20/50 SMA) extract karte hain. "
        "Phir Histogram Gradient Boosting Regressor model ke through hum future Open, High, Low, Close prices predict karte hain aur multi-day forecast trajectory banate hain with automated AI Trading Signals (Strong Buy, Buy, Hold, Sell). "
        "Frontend me maine Chart.js aur Vanilla JavaScript ke sath ek dark cyberpunk trading dashboard banaya hai jo CoinGecko aur Alternative.me se real-time multi-currency data stream karta hai.\"",
        callout_style
    ))

    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Top Technical Interview Questions & Model Answers:</b>", h2_style))
    
    qa_list = [
        ("Q1: Why did you choose FastAPI over Flask or Django?",
         "FastAPI is built on Starlette and Pydantic, making it one of the fastest Python web frameworks available (comparable to Node.js and Go). It natively supports asynchronous concurrency (async/await), automatic request validation, and self-generating OpenAPI/Swagger documentation at /docs."),
        
        ("Q2: How did you prevent data leakage during ML model training on time-series data?",
         "In financial time-series forecasting, standard random cross-validation leaks future data into past training folds. To avoid this, I used sequential time-series splitting with shuffle=False. Furthermore, all rolling indicators (SMA, RSI, MACD) are strictly computed on historical backward-looking windows."),
        
        ("Q3: Why Gradient Boosted Decision Trees over Deep Learning (LSTM / RNN)?",
         "For tabular financial data with engineered technical indicators, Gradient Boosted Trees (like HistGradientBoosting) consistently outperform Recurrent Neural Networks while requiring 100x less compute and inference time (< 80ms). They handle non-linear interactions without GPU acceleration."),
        
        ("Q4: How does the Paper Trading module calculate weighted average buy price?",
         "When a user executes subsequent BUY orders for an existing asset, the average price updates via weighted average formula: New_Avg = (Old_Total_Invested + New_Cost) / (Old_Quantity + New_Quantity). When selling, cash balance credits with Proceeds = Quantity * Live_Price, and active holdings adjust accordingly.")
    ]

    for q, a in qa_list:
        story.append(Paragraph(f"<b>{q}</b>", body_style))
        story.append(Paragraph(f"<i>Answer:</i> {a}", bullet_style))
        story.append(Spacer(1, 4))

    doc.build(story)
    print(f"✅ PDF successfully generated at: {pdf_path}")

if __name__ == "__main__":
    generate_pdf()
