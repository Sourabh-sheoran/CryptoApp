import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import init_db
from app.auth import router as auth_router
from app.market import router as market_router
from app.ml_engine import router as ml_router
from app.portfolio import router as portfolio_router

# Initialize database on startup
init_db()

app = FastAPI(
    title="CryptoPulse AI — Cryptocurrency Tracking & ML Prediction Platform",
    description="Full-stack AI-powered Crypto Market Analytics, Machine Learning Forecasting, and Paper Trading Simulator",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(market_router)
app.include_router(ml_router)
app.include_router(portfolio_router)

# Mount Static Files
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "CryptoPulse AI API is running. Static frontend not yet compiled."}

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "service": "CryptoPulse AI Python Platform",
        "version": "2.0.0",
        "features": ["Auth (JWT + SQLite)", "Real-time Markets", "XGBoost Price Prediction", "Paper Trading Simulator", "Watchlist"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
