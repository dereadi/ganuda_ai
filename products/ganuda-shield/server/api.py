#!/usr/bin/env python3
"""
Shield Collection Server — FastAPI.
Reference: stoneclad_demo_api.py (same FastAPI + PostgreSQL pattern).
Deploy: uvicorn api:app --host 0.0.0.0 --port 8443
PRIVATE — Commercial License.
"""

import json
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from anomaly import AnomalyEngine, check_missing_heartbeat

app = FastAPI(title="Ganuda Shield", description="Transparent Endpoint Monitoring — Collection Server", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# In-memory stores (swap for PostgreSQL in production deployment)
agents = {}
reports = []
anomalies_list = []
consent_records = []
anomaly_engine = AnomalyEngine()


class RegisterRequest(BaseModel):
    machine_id: str
    employee_id: str
    consent_record: dict
    agent_version: str = "0.1.0"


class HeartbeatRequest(BaseModel):
    machine_id: str
    timestamp: str


class FalseAlarmRequest(BaseModel):
    anomaly_id: int
    reason: str


def verify_api_key(x_api_key: str = Header(default="")):
    """Verify agent API key."""
    if not x_api_key:
        return None
    for agent in agents.values():
        if agent.get('api_key') == x_api_key:
            return agent
    return None


# ============================================================
# Agent Registration
# ============================================================

@app.post("/api/v1/register")
def register_agent(req: RegisterRequest):
    api_key = secrets.token_hex(32)
    encryption_key = secrets.token_urlsafe(32)

    agents[req.machine_id] = {
        'machine_id': req.machine_id,
        'employee_id': req.employee_id,
        'api_key': api_key,
        'encryption_key': encryption_key,
        'agent_version': req.agent_version,
        'status': 'active',
        'escalated': False,
        'registered_at': datetime.now(timezone.utc).isoformat(),
        'last_heartbeat': datetime.now(timezone.utc).isoformat(),
    }

    consent_records.append({
        'employee_id': req.employee_id,
        'machine_id': req.machine_id,
        'consent_timestamp': datetime.now(timezone.utc).isoformat(),
        'consent_text_hash': req.consent_record.get('consent_text_hash', ''),
        'jurisdiction': req.consent_record.get('jurisdiction', 'standard'),
        'agent_version': req.agent_version,
    })

    return {"api_key": api_key, "encryption_key": encryption_key, "status": "registered"}


# ============================================================
# Heartbeat
# ============================================================

@app.post("/api/v1/heartbeat")
def heartbeat(req: HeartbeatRequest, x_api_key: str = Header(default="")):
    if req.machine_id in agents:
        agents[req.machine_id]['last_heartbeat'] = datetime.now(timezone.utc).isoformat()
        return {"status": "ok"}
    raise HTTPException(status_code=404, detail="Agent not registered")


# ============================================================
# Activity Report Ingestion
# ============================================================

@app.post("/api/v1/report")
async def receive_report(
    request: Request,
    x_api_key: str = Header(default=""),
    x_machine_id: str = Header(default=""),
    x_encrypted: str = Header(default="false"),
    x_batch_size: str = Header(default="1"),
):
    body = await request.body()

    # Decrypt if needed (in production, use the agent's encryption key)
    if x_encrypted == "true":
        # For P-3, store encrypted blob. Decryption in P-2 with proper key management.
        report_data = {"encrypted_blob": True, "size": len(body)}
    else:
        try:
            report_data = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON")

    # Store report
    report = {
        'machine_id': x_machine_id,
        'employee_id': agents.get(x_machine_id, {}).get('employee_id', 'unknown'),
        'report_timestamp': datetime.now(timezone.utc).isoformat(),
        'report_data': report_data,
        'batch_size': int(x_batch_size),
        'encrypted': x_encrypted == "true",
    }
    reports.append(report)

    # Run anomaly detection on each snapshot in batch
    if isinstance(report_data, list):
        for snapshot in report_data:
            detected = anomaly_engine.evaluate(snapshot)
            for a in detected:
                a['id'] = len(anomalies_list)
                anomalies_list.append(a)

    return {"status": "received", "batch_size": int(x_batch_size)}


# ============================================================
# Config (allows server-side escalation)
# ============================================================

@app.get("/api/v1/config/{machine_id}")
def get_agent_config(machine_id: str, x_api_key: str = Header(default="")):
    agent = agents.get(machine_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {
        'escalated': agent.get('escalated', False),
        'escalation_reason': agent.get('escalation_reason'),
        'screenshots_enabled': agent.get('escalated', False),
        'clipboard_content_enabled': agent.get('escalated', False),
    }


# ============================================================
# Anomaly Management
# ============================================================

@app.get("/api/v1/anomalies")
def get_anomalies(severity: Optional[str] = None, limit: int = 50):
    filtered = anomalies_list
    if severity:
        filtered = [a for a in filtered if a.get('severity') == severity]
    return filtered[-limit:]


@app.post("/api/v1/anomaly/ack")
def acknowledge_anomaly(anomaly_id: int, action: str = "ack", admin_user: str = "admin"):
    if anomaly_id < len(anomalies_list):
        anomalies_list[anomaly_id]['admin_action'] = action
        anomalies_list[anomaly_id]['admin_user'] = admin_user
        anomalies_list[anomaly_id]['admin_timestamp'] = datetime.now(timezone.utc).isoformat()
        return {"status": "acknowledged"}
    raise HTTPException(status_code=404, detail="Anomaly not found")


@app.post("/api/v1/employee/false-alarm")
def report_false_alarm(req: FalseAlarmRequest, x_api_key: str = Header(default="")):
    if req.anomaly_id < len(anomalies_list):
        anomalies_list[req.anomaly_id]['employee_flagged_false'] = True
        anomalies_list[req.anomaly_id]['employee_false_reason'] = req.reason
        return {"status": "flagged"}
    raise HTTPException(status_code=404, detail="Anomaly not found")


# ============================================================
# Admin Dashboard
# ============================================================

@app.get("/", response_class=HTMLResponse)
def dashboard():
    agent_rows = ""
    for mid, agent in agents.items():
        status_color = "#68d391" if agent.get('status') == 'active' else "#fc8181"
        escalated = "🔴 ESCALATED" if agent.get('escalated') else "🟢 Normal"
        agent_rows += f"""<tr>
            <td>{mid}</td><td>{agent.get('employee_id','?')}</td>
            <td style="color:{status_color}">{agent.get('status','?')}</td>
            <td>{escalated}</td>
            <td>{str(agent.get('last_heartbeat','?'))[:19]}</td></tr>\n"""

    anomaly_rows = ""
    for a in reversed(anomalies_list[-20:]):
        sev_color = {"critical":"#fc8181","warning":"#f6ad55","info":"#68d391"}.get(a.get('severity'),'#a0aec0')
        anomaly_rows += f"""<tr>
            <td style="color:{sev_color}">{a.get('severity','?')}</td>
            <td>{a.get('anomaly_type','?')}</td>
            <td>{a.get('employee_id','?')}</td>
            <td>{a.get('description','')[:60]}</td>
            <td>{str(a.get('detected_at',''))[:19]}</td></tr>\n"""

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Ganuda Shield — Admin Dashboard</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,sans-serif;background:#2d3748;color:#e2e8f0;padding:2rem}}
h1{{color:#d4a843;margin-bottom:1rem}}h2{{color:#4fd1c5;margin:1.5rem 0 0.5rem}}
table{{width:100%;border-collapse:collapse;margin:0.5rem 0}}th,td{{padding:0.5rem;text-align:left;border-bottom:1px solid #4a5568}}
th{{color:#d4a843;font-size:0.85rem}}td{{font-size:0.85rem}}.footer{{text-align:center;margin-top:2rem;color:#a0aec0;font-size:0.8rem}}</style></head>
<body><h1>Ganuda Shield</h1>
<p style="color:#a0aec0">Agents: {len(agents)} | Reports: {len(reports)} | Anomalies: {len(anomalies_list)}</p>
<h2>Registered Agents</h2>
<table><tr><th>Machine</th><th>Employee</th><th>Status</th><th>Monitoring</th><th>Last Heartbeat</th></tr>
{agent_rows if agent_rows else '<tr><td colspan="5">No agents registered</td></tr>'}
</table>
<h2>Recent Anomalies</h2>
<table><tr><th>Severity</th><th>Type</th><th>Employee</th><th>Description</th><th>Detected</th></tr>
{anomaly_rows if anomaly_rows else '<tr><td colspan="5">No anomalies detected</td></tr>'}
</table>
<div class="footer">Ganuda Shield — Transparent Endpoint Monitoring | Both hands on the shield | For Seven Generations</div>
</body></html>"""


@app.get("/health")
def health():
    return {
        "status": "alive",
        "service": "ganuda-shield",
        "agents": len(agents),
        "reports": len(reports),
        "anomalies": len(anomalies_list),
    }
