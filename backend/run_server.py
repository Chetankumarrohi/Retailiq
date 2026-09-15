"""
Convenience script to start the RetailIQ FastAPI backend server.
Ensures correct PYTHONPATH for module imports.
Run from project root: python backend/run_server.py
"""
import sys
import os
from pathlib import Path

# Add project root to Python path so 'backend.app.*' and 'src.*' imports resolve
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("PYTHONPATH", str(PROJECT_ROOT))

if __name__ == "__main__":
    import uvicorn
    print(f"[RetailIQ] Starting server from project root: {PROJECT_ROOT}")
    print(f"[RetailIQ] Database: {PROJECT_ROOT / 'retailiq.db'}")
    print(f"[RetailIQ] Model: {PROJECT_ROOT / 'models' / 'trained' / 'retailiq_forecaster.pkl'}")
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(PROJECT_ROOT / "backend")],
    )
