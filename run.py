#!/usr/bin/env python3
"""
CryptoPulse AI — Single-command Runner
Runs the full-stack Python application (FastAPI backend + ML Engine + Static Dashboard)
"""
import sys
import os
import uvicorn

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "127.0.0.1")
    print("\n" + "="*60)
    print(" 🚀 Starting CryptoPulse AI Full-Stack Python Platform")
    print(f" 🌐 Web Dashboard: http://localhost:{port}")
    print(f" 📖 Swagger API Docs: http://localhost:{port}/docs")
    print("="*60 + "\n")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
