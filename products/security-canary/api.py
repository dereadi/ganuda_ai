#!/usr/bin/env python3
"""
Desktop Security Canary — FastAPI Backend
Serves the demo report at ganuda.us/canary

Deploy: uvicorn api:app --host 0.0.0.0 --port 8502
MOCHA Sprint — Apr 4, 2026
"""

import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Desktop Security Canary",
    description="Is Your Machine Safe? — Sovereign security scanner",
    version="0.1.0-mocha",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DEMO_REPORT_PATH = Path(__file__).parent / "demo-report.html"
DEMO_JSON_PATH = Path(__file__).parent / "demo-results.json"


@app.get("/", response_class=HTMLResponse)
def landing():
    """Serve the demo HTML report."""
    if DEMO_REPORT_PATH.exists():
        return HTMLResponse(content=DEMO_REPORT_PATH.read_text())
    return HTMLResponse(content="<h1>Security Canary</h1><p>No demo report generated yet.</p>")


@app.get("/health")
def health():
    return {"status": "alive", "service": "security-canary"}


@app.get("/demo")
def demo_json():
    """Return demo scan results as JSON."""
    if DEMO_JSON_PATH.exists():
        return json.loads(DEMO_JSON_PATH.read_text())
    return {"error": "No demo results cached. Run canary.py first."}
