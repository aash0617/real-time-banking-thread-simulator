"""
main.py
--------
FastAPI application entry point.

Run:
  pip install fastapi uvicorn
  uvicorn main:app --reload --port 8000

API docs auto-generated at:
  http://localhost:8000/docs    (Swagger UI)
  http://localhost:8000/redoc  (ReDoc)
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from api_routes import router

app = FastAPI(
    title       = "Banking Transaction Simulator",
    description = "Real-Time Multithreaded Banking Transaction Processing Simulator "
                  "demonstrating OS concepts: threading, scheduling, synchronization.",
    version     = "1.0.0",
)

# ── CORS: allow the React frontend to call this API ───────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins    = ["http://localhost:5173",   # Vite default
                        "http://localhost:3000"],   # CRA / alternative
    allow_credentials= True,
    allow_methods    = ["*"],
    allow_headers    = ["*"],
)

# ── Mount all routes ──────────────────────────────────────────────────────────
app.include_router(router, prefix="/api")


@app.get("/")
def root():
  ui_path = Path(__file__).parent / "ui_final.html"
  if ui_path.exists():
    return FileResponse(ui_path)

  return {
    "message": "Banking Transaction Simulator API",
    "docs"   : "/docs",
    "api"    : "/api",
    "note"   : "ui_final.html not found in project root",
  }
