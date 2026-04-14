#!/usr/bin/env python3
"""
Meeting Notes Extractor — FastAPI Backend
Serves demo report at ganuda.us/meeting-notes

Deploy: uvicorn api:app --host 0.0.0.0 --port 8503
MOCHA Sprint — Apr 4, 2026
"""

import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Meeting Notes Extractor",
    description="What Did We Decide? — Sovereign meeting intelligence",
    version="0.1.0-mocha",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DEMO_REPORT = Path(__file__).parent / "demo-report.html"


@app.get("/", response_class=HTMLResponse)
def landing():
    if DEMO_REPORT.exists():
        return HTMLResponse(content=DEMO_REPORT.read_text())
    return HTMLResponse(content="<h1>Meeting Notes Extractor</h1><p>No demo report yet.</p>")


@app.get("/health")
def health():
    return {"status": "alive", "service": "meeting-notes-extractor"}
