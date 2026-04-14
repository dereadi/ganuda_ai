#!/usr/bin/env python3
"""
Subscription Trimmer — FastAPI Backend
"What Am I Paying For?"

Endpoints:
  GET  /              — Landing page
  POST /scan          — Trigger a real Gmail scan + LLM classification
  GET  /results/{id}  — Get scan results
  GET  /demo          — Pre-cached demo results

Deploy: uvicorn api:app --host 0.0.0.0 --port 8501
MOCHA Sprint — Apr 2, 2026
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Lazy imports — scanner needs google-auth which may not be on DMZ node
# Scan runs on redfin where Gmail token lives; DMZ serves dashboard + demo cache
try:
    from scanner import scan_subscriptions, filter_noise, group_by_service
    from classifier import classify_batch
    from aggregator import aggregate_subscriptions
    SCAN_AVAILABLE = True
except ImportError:
    SCAN_AVAILABLE = False

app = FastAPI(
    title="Subscription Trimmer",
    description="What Am I Paying For? — Sovereign subscription scanner",
    version="0.1.0-mocha",
)

# In-memory results store (swap for Redis/DB later)
scan_jobs = {}

DEMO_RESULTS_PATH = Path(__file__).parent / "demo_results.json"
TEMPLATES_PATH = Path(__file__).parent / "templates"


# ============================================================
# Models
# ============================================================

class ScanRequest(BaseModel):
    months_back: Optional[int] = 6
    max_results: Optional[int] = 200


# ============================================================
# Background scan task
# ============================================================

def run_scan(job_id: str, months_back: int, max_results: int):
    """Background task: scan → classify → aggregate."""
    try:
        scan_jobs[job_id] = {"status": "scanning", "progress": "Fetching emails from Gmail..."}

        # Step 1: Scan Gmail
        signals = scan_subscriptions(months_back=months_back, max_results=max_results)
        filtered = filter_noise(signals)

        scan_jobs[job_id] = {"status": "classifying", "progress": f"Classifying {len(filtered)} emails with LLM..."}

        # Step 2: Classify with LLM
        classified = classify_batch(filtered, verbose=False)

        # Step 3: Filter to subscriptions only
        subscriptions = [c for c in classified if c.get('is_subscription')]

        scan_jobs[job_id] = {"status": "aggregating", "progress": "Calculating totals..."}

        # Step 4: Aggregate
        result = aggregate_subscriptions(
            email="dereadi@gmail.com",
            scan_date=datetime.now().strftime("%Y-%m-%d"),
            subscriptions=subscriptions
        )

        # Store results
        scan_jobs[job_id] = {"status": "complete", "result": result}

        # Also save as demo cache
        with open(DEMO_RESULTS_PATH, 'w') as f:
            json.dump(result, f, indent=2, default=str)

    except Exception as e:
        scan_jobs[job_id] = {"status": "error", "error": str(e)}


# ============================================================
# Routes
# ============================================================

@app.get("/", response_class=HTMLResponse)
def landing_page():
    """Serve the dashboard HTML."""
    html_path = TEMPLATES_PATH / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text())
    return HTMLResponse(content="<h1>Subscription Trimmer</h1><p>Dashboard not found.</p>")


@app.post("/scan")
def trigger_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """Trigger a real Gmail scan. Returns job_id to poll for results."""
    if not SCAN_AVAILABLE:
        raise HTTPException(status_code=503, detail="Scanner not available on this node. Gmail token lives on redfin. Use /demo for cached results.")
    job_id = hashlib.md5(f"{datetime.now().isoformat()}".encode()).hexdigest()[:12]
    scan_jobs[job_id] = {"status": "queued"}
    background_tasks.add_task(run_scan, job_id, request.months_back, request.max_results)
    return {"job_id": job_id, "status": "queued", "poll": f"/results/{job_id}"}


@app.get("/results/{job_id}")
def get_results(job_id: str):
    """Get scan results by job ID."""
    if job_id not in scan_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return scan_jobs[job_id]


@app.get("/demo")
def demo_results():
    """Return pre-cached demo results."""
    if DEMO_RESULTS_PATH.exists():
        with open(DEMO_RESULTS_PATH) as f:
            return json.load(f)
    return {"error": "No demo results cached. Run a scan first via POST /scan"}


@app.get("/health")
def health():
    return {
        "status": "alive",
        "service": "subscription-trimmer",
        "active_scans": sum(1 for j in scan_jobs.values() if j.get("status") not in ("complete", "error")),
        "completed_scans": sum(1 for j in scan_jobs.values() if j.get("status") == "complete"),
    }
