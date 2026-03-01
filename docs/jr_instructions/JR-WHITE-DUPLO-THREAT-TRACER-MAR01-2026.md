# JR Instruction: White Duplo — Threat Tracer Enzyme

**Task**: WHITE-DUPLO-001
**Title**: White Duplo Defensive Enzyme (Immune Active Response)
**Priority**: 2
**Assigned Jr**: Software Engineer Jr.
**Long Man Phase**: BUILD

## Context

In biology, white blood cells (leukocytes) are the adaptive immune system. They don't just detect threats — they pursue, identify, trace to source, and alert. The White Duplo is this function for the federation.

Crawdad and Coyote are the **innate immune system** — pattern recognition, concern flags, anomaly detection. The White Duplo is the **adaptive immune response** — when a threat is detected, it activates as an enzyme, traces the threat back to origin, gathers forensic evidence, and alerts the operator.

This is a Duplo enzyme (not an agent). It is invoked, it traces, it reports, it's done. No persistent state. No autonomous hunting.

### Threat Types It Handles

| Threat | Source Signal | Trace Method |
|---|---|---|
| Failed auth attempts | Gateway access logs, fail2ban | IP geolocation, rate analysis, pattern matching against known scanners |
| Prompt injection attempts | Gateway input validation, specialist concern flags | Extract payload, classify attack type, check thermal for similar patterns |
| Credential probing | SSH logs, FreeIPA audit logs | Source IP, timing analysis, credential target mapping |
| Anomalous API patterns | Gateway rate limiting, unusual endpoint access | Caller ID analysis, temporal pattern, payload inspection |
| Model extraction attempts | High-volume inference requests from single caller | Token consumption analysis (ATP counter), request pattern forensics |

## Files

Create `lib/duplo/context_profiles/white_duplo.yaml`

```yaml
# White Duplo — Threat Tracer Enzyme (Leukocyte)
# Adaptive immune response: trace threats to source, gather forensics, alert operator
#
# Invoked by: Crawdad concern flags, gateway alerts, fail2ban triggers
# Returns: threat report with source attribution, severity, and recommended action

name: white_duplo
description: Threat tracer enzyme — traces attacks to source, gathers forensics, alerts operator
default_model: qwen
max_tokens: 1024
temperature: 0.1

system_prompt: |
  You are a threat tracer for the Cherokee AI Federation's immune system.
  When invoked, you have been given evidence of a potential security threat.

  Your job:
  1. IDENTIFY the threat type (auth probe, prompt injection, credential stuffing, extraction attempt, other)
  2. TRACE the source (IP, caller ID, API key, temporal pattern)
  3. ASSESS severity (CRITICAL / HIGH / MEDIUM / LOW)
  4. GATHER evidence (relevant log lines, payloads, patterns)
  5. RECOMMEND action (block IP, revoke key, rate limit, monitor, escalate to Chief)

  Output format:
  THREAT_TYPE: [type]
  SOURCE: [source identification]
  SEVERITY: [level]
  EVIDENCE:
  - [evidence item 1]
  - [evidence item 2]
  TIMELINE: [when the threat started, progression]
  RECOMMENDATION: [specific action]
  ALERT: [true/false — should operator be notified immediately?]

  Be precise. Cite specific data. Do not speculate beyond the evidence.
  If evidence is insufficient to trace, say so — do not fabricate attribution.

  DC-5 applies: your analysis is observable. Log everything.

tool_set:
  - execute_db_query
  - query_thermal_semantic
  - write_thermal
```

Create `lib/duplo/white_duplo.py`

```python
"""
White Duplo — Threat Tracer Enzyme (Leukocyte)
Cherokee AI Federation — The Living Cell Architecture

Active immune response: when a threat is detected by Crawdad, Coyote,
or the gateway, the White Duplo traces it to source and alerts.

This is an enzyme, not an agent. Invoke → trace → report → done.

Usage:
    from lib.duplo.white_duplo import trace_threat

    report = trace_threat(
        threat_signal="5 failed SSH attempts from 203.0.113.42 in 30 seconds",
        source_type="ssh_auth",
        caller_id="crawdad_alert",
    )
    # report = {product, severity, alert, ...}
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("duplo.white_duplo")


def _gather_context(threat_signal: str, source_type: str) -> str:
    """Gather additional context from federation systems for threat analysis."""
    context_parts = [f"Threat Signal: {threat_signal}", f"Source Type: {source_type}"]

    try:
        from lib.ganuda_db import execute_query

        # Recent failed auth attempts from api_audit_log
        if source_type in ("ssh_auth", "api_auth", "gateway_auth"):
            rows = execute_query("""
                SELECT caller_ip, endpoint, status_code, created_at
                FROM api_audit_log
                WHERE status_code >= 400
                  AND created_at > NOW() - INTERVAL '1 hour'
                ORDER BY created_at DESC
                LIMIT 20
            """)
            if rows:
                context_parts.append("Recent failed requests (last hour):")
                for r in rows[:10]:
                    d = dict(r)
                    context_parts.append(
                        f"  {d.get('created_at')} | {d.get('caller_ip')} | "
                        f"{d.get('endpoint')} | {d.get('status_code')}"
                    )

        # Recent thermal alerts
        rows = execute_query("""
            SELECT original_content, temperature_score, created_at
            FROM thermal_memory_archive
            WHERE original_content ILIKE '%%threat%%'
               OR original_content ILIKE '%%attack%%'
               OR original_content ILIKE '%%unauthorized%%'
            ORDER BY created_at DESC
            LIMIT 5
        """)
        if rows:
            context_parts.append("Recent security thermals:")
            for r in rows:
                d = dict(r)
                context_parts.append(
                    f"  [{d.get('temperature_score')}] {str(d.get('original_content', ''))[:200]}"
                )

    except Exception as e:
        context_parts.append(f"Context gathering partial failure: {e}")

    return "\n".join(context_parts)


def trace_threat(
    threat_signal: str,
    source_type: str = "unknown",
    caller_id: str = "immune_system",
    alert_callback=None,
) -> dict:
    """
    Trace a threat to source using the White Duplo enzyme.

    Args:
        threat_signal: Description of the detected threat
        source_type: Category (ssh_auth, api_auth, prompt_injection, extraction, anomaly)
        caller_id: Who/what triggered the trace
        alert_callback: Optional function(report_dict) called if ALERT=true

    Returns:
        dict with: product, severity, alert, tokens, latency_ms, success
    """
    from lib.duplo.composer import compose_enzyme

    start = time.time()

    # Gather context from federation systems
    context = _gather_context(threat_signal, source_type)

    # Compose and invoke the White Duplo enzyme
    enzyme = compose_enzyme("white_duplo", caller_id=caller_id)
    substrate = f"{context}\n\nAnalyze this threat. Trace to source. Assess severity. Recommend action."

    result = enzyme(substrate)

    # Parse severity and alert flag from the product
    product = result.get("product", "") or ""
    severity = "UNKNOWN"
    should_alert = False

    for line in product.split("\n"):
        line_stripped = line.strip()
        if line_stripped.startswith("SEVERITY:"):
            severity = line_stripped.split(":", 1)[1].strip()
        if line_stripped.startswith("ALERT:"):
            should_alert = "true" in line_stripped.lower()

    # Thermalize the threat report
    try:
        from lib.ganuda_db import safe_thermal_write
        temp = {"CRITICAL": 95.0, "HIGH": 85.0, "MEDIUM": 70.0, "LOW": 55.0}.get(severity, 65.0)
        safe_thermal_write(
            content=f"WHITE DUPLO THREAT TRACE — {source_type}\nSeverity: {severity}\n{product[:2000]}",
            temperature=temp,
            source="white_duplo",
            sacred=(severity == "CRITICAL"),
            metadata={
                "type": "threat_trace",
                "source_type": source_type,
                "severity": severity,
                "caller_id": caller_id,
                "alert": should_alert,
            },
        )
    except Exception as e:
        logger.warning(f"Failed to thermalize threat report: {e}")

    # Fire alert callback if threat warrants it
    if should_alert and alert_callback:
        try:
            alert_callback({
                "severity": severity,
                "source_type": source_type,
                "report": product[:2000],
                "timestamp": datetime.now().isoformat(),
            })
        except Exception as e:
            logger.error(f"Alert callback failed: {e}")

    report = {
        "product": product,
        "severity": severity,
        "alert": should_alert,
        "source_type": source_type,
        "tokens": result.get("tokens", {}),
        "latency_ms": result.get("latency_ms", 0),
        "success": result.get("success", False),
    }

    logger.info(
        f"White Duplo trace complete: {source_type} | {severity} | "
        f"alert={should_alert} | {result.get('latency_ms', 0)}ms"
    )

    return report
```

## Integration Points (future Jr tasks, not this one)

1. **Gateway hook**: On 5+ failed auth in 60s from same IP, invoke `trace_threat(source_type="gateway_auth")`
2. **Crawdad concern flag**: When council vote returns SECURITY CONCERN, invoke `trace_threat(source_type="prompt_injection")`
3. **Telegram alert**: Pass `telegram_notify` as `alert_callback` for CRITICAL/HIGH severity
4. **fail2ban integration**: Parse fail2ban log, invoke on repeat offenders

## Verification

1. Import: `python3 -c "from lib.duplo.white_duplo import trace_threat; print('OK')"`
2. YAML parse: `python3 -c "import yaml; yaml.safe_load(open('lib/duplo/context_profiles/white_duplo.yaml')); print('Valid')"`
3. Dry run (requires vLLM + DB):
   ```text
   python3 -c "
   from lib.duplo.white_duplo import trace_threat
   r = trace_threat(
       threat_signal='10 failed login attempts from 203.0.113.42 targeting /api/v1/council in 30 seconds',
       source_type='gateway_auth',
       caller_id='test',
   )
   print(f'Severity: {r[\"severity\"]}, Alert: {r[\"alert\"]}')
   print(r['product'][:500])
   "
   ```
