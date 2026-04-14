#!/usr/bin/env python3
"""
Clipboard Intelligence — FastAPI Backend
Dashboard + API at ganuda.us/clipboard

Deploy: uvicorn api:app --host 0.0.0.0 --port 8504
MOCHA Sprint — Apr 4, 2026
"""

import sqlite3
import os
import json
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Clipboard Intelligence",
    description="What Did I Copy? — Sovereign clipboard knowledge base",
    version="0.1.0-mocha",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DB_PATH = os.path.expanduser("~/.clipboard_intel/clips.db")
DEMO_PATH = Path(__file__).parent / "demo-results.json"


def get_db():
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/", response_class=HTMLResponse)
def dashboard():
    """Serve the clipboard dashboard."""
    html_path = Path(__file__).parent / "templates" / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text())

    # Inline minimal dashboard if template not found
    return HTMLResponse(content="""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Clipboard Intelligence</title>
<style>*{margin:0;padding:0;box-sizing:border-box}:root{--navy:#1a365d;--charcoal:#2d3748;--gold:#d4a843;--teal:#4fd1c5;--text:#e2e8f0;--muted:#a0aec0}
body{font-family:-apple-system,sans-serif;background:var(--charcoal);color:var(--text);line-height:1.6}
a{color:var(--teal)}.header{background:var(--navy);padding:2rem;text-align:center;border-bottom:2px solid var(--gold)}
.header h1{color:var(--gold);font-size:1.5rem}.header p{color:var(--muted);font-size:0.85rem}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:1rem;max-width:700px;margin:1.5rem auto;padding:0 1rem}
.stat{background:rgba(26,54,93,0.6);border:1px solid rgba(212,168,67,0.3);border-radius:8px;padding:0.8rem;text-align:center}
.stat .num{font-size:1.8rem;font-weight:700;color:var(--gold)}.stat .label{font-size:0.7rem;color:var(--muted)}
.clips{max-width:700px;margin:1rem auto;padding:0 1rem}
.clip{display:flex;justify-content:space-between;align-items:center;padding:0.7rem;margin:0.3rem 0;background:rgba(26,54,93,0.4);border-radius:6px;border-left:3px solid var(--teal)}
.clip.sensitive{border-left-color:#fc8181}.clip .type{color:var(--muted);font-size:0.75rem;min-width:80px}
.clip .preview{flex:1;font-size:0.85rem;margin:0 0.5rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.clip .temp{font-size:0.75rem;color:var(--gold);min-width:40px;text-align:right}
.footer{text-align:center;padding:2rem;color:var(--muted);font-size:0.8rem}</style></head>
<body><div class="header"><h1>Clipboard Intelligence</h1><p>What Did I Copy? — Temperature-scored clipboard history</p></div>
<div class="stats"><div class="stat"><div class="num" id="s-total">—</div><div class="label">Total Clips</div></div>
<div class="stat"><div class="num" id="s-today">—</div><div class="label">Today</div></div>
<div class="stat"><div class="num" id="s-temp">—</div><div class="label">Avg Temp</div></div>
<div class="stat"><div class="num" id="s-sensitive">—</div><div class="label">Sensitive</div></div></div>
<div class="clips" id="clip-list"></div>
<div class="footer"><p>Built by <a href="https://ganuda.us">Cherokee AI Federation</a> — sovereign, no cloud</p></div>
<script>
async function load(){
 try{const s=await fetch('/api/stats').then(r=>r.json());
 document.getElementById('s-total').textContent=s.total;
 document.getElementById('s-today').textContent=s.today;
 document.getElementById('s-temp').textContent=s.avg_temperature+'°';
 document.getElementById('s-sensitive').textContent=s.sensitive;}catch(e){}
 try{const c=await fetch('/api/clips?limit=20').then(r=>r.json());
 const el=document.getElementById('clip-list');
 el.innerHTML=c.map(clip=>'<div class="clip'+(clip.is_sensitive?' sensitive':'')+'">'+
 '<span class="type">'+clip.clip_type+'</span>'+
 '<span class="preview">'+clip.content_preview+'</span>'+
 '<span class="temp">'+clip.temperature.toFixed(0)+'°</span></div>').join('');}catch(e){}}
load();setInterval(load,10000);
</script></body></html>""")


@app.get("/health")
def health():
    return {"status": "alive", "service": "clipboard-intelligence"}


@app.get("/api/stats")
def stats():
    conn = get_db()
    if not conn:
        if DEMO_PATH.exists():
            return json.loads(DEMO_PATH.read_text()).get("stats", {})
        return {"total": 0, "avg_temperature": 0, "today": 0, "sensitive": 0, "by_type": {}}

    cur = conn.execute("SELECT COUNT(*), AVG(temperature) FROM clips")
    total, avg_t = cur.fetchone()
    cur = conn.execute("SELECT clip_type, COUNT(*) FROM clips GROUP BY clip_type ORDER BY COUNT(*) DESC")
    by_type = dict(cur.fetchall())
    cur = conn.execute("SELECT COUNT(*) FROM clips WHERE is_sensitive = 1")
    sensitive = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM clips WHERE timestamp > datetime('now', '-1 day')")
    today = cur.fetchone()[0]
    conn.close()
    return {"total": total or 0, "avg_temperature": round(avg_t or 0, 1),
            "today": today, "sensitive": sensitive, "by_type": by_type}


@app.get("/api/clips")
def get_clips(query: str = None, clip_type: str = None, limit: int = Query(default=20, le=100)):
    conn = get_db()
    if not conn:
        if DEMO_PATH.exists():
            return json.loads(DEMO_PATH.read_text()).get("clips", [])[:limit]
        return []

    sql = "SELECT id, content_preview, clip_type, temperature, is_sensitive, is_pinned, timestamp FROM clips WHERE 1=1"
    params = []
    if query:
        sql += " AND (content LIKE ? OR content_preview LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])
    if clip_type:
        sql += " AND clip_type = ?"
        params.append(clip_type)
    sql += " ORDER BY temperature DESC, timestamp DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/demo")
def demo():
    if DEMO_PATH.exists():
        return json.loads(DEMO_PATH.read_text())
    return {"error": "No demo data. Run the monitor to collect clips."}
