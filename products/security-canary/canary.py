#!/usr/bin/env python3
"""
Desktop Security Canary — "Is Your Machine Safe?"
Main CLI runner. Scans ports, credentials, and configs. Generates HTML report.

Usage:
    python3 canary.py                  # Full scan + HTML report
    python3 canary.py --quick          # Port scan + cred scan only
    python3 canary.py --output report.html  # Custom output path
    python3 canary.py --json           # JSON output instead of HTML

MOCHA Sprint — Apr 4, 2026
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from port_scanner import scan_listening_ports
from cred_scanner import run_credential_scan
from config_checker import run_config_check


def run_full_scan(quick=False):
    """Run all scanners and aggregate results."""
    results = {
        "scan_date": datetime.now().isoformat(),
        "hostname": os.uname().nodename,
        "platform": sys.platform,
        "sections": {},
        "summary": {"critical": 0, "warning": 0, "info": 0, "total": 0},
    }

    # Port scan (always)
    print("Scanning ports...", file=sys.stderr)
    ports = scan_listening_ports()
    results["sections"]["ports"] = {
        "title": "Listening Ports",
        "findings": ports,
    }

    # Credential scan (always)
    print("Scanning for exposed credentials...", file=sys.stderr)
    creds = run_credential_scan()
    results["sections"]["credentials"] = {
        "title": "Credential Exposure",
        "findings": creds,
    }

    # Config check (skip in quick mode)
    if not quick:
        print("Checking system configuration...", file=sys.stderr)
        configs = run_config_check()
        results["sections"]["config"] = {
            "title": "System Configuration",
            "findings": configs,
        }

    # Tally severities
    for section in results["sections"].values():
        for finding in section["findings"]:
            sev = finding.get("severity", "info")
            results["summary"][sev] = results["summary"].get(sev, 0) + 1
            results["summary"]["total"] += 1

    return results


def generate_html_report(results, output_path="security-report.html"):
    """Generate single-file HTML report with ganuda.us styling."""

    severity_colors = {
        "critical": "#fc8181",
        "warning": "#f6ad55",
        "info": "#68d391",
    }
    severity_icons = {
        "critical": "&#x1F534;",
        "warning": "&#x1F7E1;",
        "info": "&#x1F7E2;",
    }

    findings_html = ""
    for section_key, section in results["sections"].items():
        findings_html += f'<div class="section-title">{section["title"]}</div>\n'
        for f in section["findings"]:
            sev = f.get("severity", "info")
            color = severity_colors.get(sev, "#a0aec0")
            icon = severity_icons.get(sev, "&#x26AA;")

            desc = f.get("description", f.get("risk", ""))
            location = f.get("location", "")
            if f.get("port"):
                location = f":{f['port']} ({f.get('process', '?')})"
            fix = f.get("fix", "")

            findings_html += f'''<div class="finding" style="border-left-color:{color}">
  <div class="finding-header">
    <span>{icon} <strong>{sev.upper()}</strong></span>
    <span class="finding-type">{f.get("type", f.get("service", f.get("check", "")))}</span>
  </div>
  <div class="finding-desc">{desc}</div>
  {"<div class='finding-location'>Location: " + location + "</div>" if location else ""}
  {"<div class='finding-fix'>Fix: <code>" + fix + "</code></div>" if fix else ""}
</div>
'''

    s = results["summary"]
    score = "CRITICAL" if s["critical"] > 0 else "WARNING" if s["warning"] > 0 else "CLEAN"
    score_color = severity_colors.get("critical" if s["critical"] > 0 else "warning" if s["warning"] > 0 else "info")

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Security Canary Report — {results["hostname"]}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  :root {{ --navy:#1a365d; --charcoal:#2d3748; --gold:#d4a843; --teal:#4fd1c5; --text:#e2e8f0; --muted:#a0aec0; }}
  body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; background:var(--charcoal); color:var(--text); line-height:1.6; }}
  a {{ color:var(--teal); text-decoration:none; }}
  .header {{ background:var(--navy); padding:2rem; text-align:center; border-bottom:2px solid var(--gold); }}
  .header h1 {{ color:var(--gold); font-size:1.5rem; }}
  .header .score {{ font-size:2rem; font-weight:700; color:{score_color}; margin-top:0.5rem; }}
  .header .meta {{ color:var(--muted); font-size:0.8rem; margin-top:0.3rem; }}
  .stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:1rem; max-width:700px; margin:1.5rem auto; padding:0 1rem; }}
  .stat {{ background:rgba(26,54,93,0.6); border:1px solid rgba(212,168,67,0.3); border-radius:8px; padding:0.8rem; text-align:center; }}
  .stat .num {{ font-size:1.5rem; font-weight:700; }}
  .stat .label {{ font-size:0.7rem; color:var(--muted); }}
  .section-title {{ max-width:700px; margin:1.5rem auto 0.5rem; padding:0 1rem; color:var(--gold); font-weight:600; font-size:1.1rem; }}
  .finding {{ max-width:700px; margin:0.4rem auto; padding:0.8rem; background:rgba(26,54,93,0.4); border-left:3px solid var(--muted); border-radius:0 6px 6px 0; }}
  .finding-header {{ display:flex; justify-content:space-between; font-size:0.85rem; }}
  .finding-type {{ color:var(--muted); font-size:0.75rem; }}
  .finding-desc {{ margin-top:0.3rem; font-size:0.85rem; }}
  .finding-location {{ color:var(--muted); font-size:0.75rem; margin-top:0.2rem; }}
  .finding-fix {{ color:var(--teal); font-size:0.8rem; margin-top:0.3rem; }}
  .finding-fix code {{ background:rgba(0,0,0,0.3); padding:0.1rem 0.4rem; border-radius:3px; font-size:0.75rem; }}
  .footer {{ text-align:center; padding:2rem; color:var(--muted); font-size:0.8rem; }}
</style>
</head>
<body>
<div class="header">
  <h1>Desktop Security Canary</h1>
  <div class="score">{score}</div>
  <div class="meta">{results["hostname"]} | {results["scan_date"][:19]} | {results["platform"]}</div>
</div>
<div class="stats">
  <div class="stat"><div class="num" style="color:#fc8181">{s["critical"]}</div><div class="label">Critical</div></div>
  <div class="stat"><div class="num" style="color:#f6ad55">{s["warning"]}</div><div class="label">Warning</div></div>
  <div class="stat"><div class="num" style="color:#68d391">{s["info"]}</div><div class="label">Info</div></div>
  <div class="stat"><div class="num" style="color:var(--gold)">{s["total"]}</div><div class="label">Total</div></div>
</div>
{findings_html}
<div class="footer">
  <p>Scanned locally by <a href="https://ganuda.us">Desktop Security Canary</a> — no data left this machine</p>
  <p style="margin-top:0.5rem;">Cherokee AI Federation | For Seven Generations</p>
</div>
</body>
</html>'''

    Path(output_path).write_text(html)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Desktop Security Canary — Is Your Machine Safe?")
    parser.add_argument("--quick", action="store_true", help="Port + credential scan only")
    parser.add_argument("--output", default=None, help="Output HTML report path")
    parser.add_argument("--json", action="store_true", help="JSON output to stdout")
    args = parser.parse_args()

    results = run_full_scan(quick=args.quick)

    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        output = args.output or f"security-report-{datetime.now().strftime('%Y-%m-%d')}.html"
        generate_html_report(results, output)
        print(f"\nReport saved to: {output}")
        print(f"  Critical: {results['summary']['critical']}")
        print(f"  Warning:  {results['summary']['warning']}")
        print(f"  Info:     {results['summary']['info']}")


if __name__ == '__main__':
    main()
