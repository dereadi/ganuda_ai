#!/usr/bin/env python3
"""
Smoke Test — ganuda.us via Playwright (real browser).

Verifies that pages load, content is fresh, cache headers are correct,
and no stale content is served. Screenshot on failure.

Usage:
    python3 scripts/smoke_test_ganuda_us.py
    python3 scripts/smoke_test_ganuda_us.py --screenshot-all
"""

import sys
import os
import time
import json
import argparse
from datetime import datetime

# Playwright is npx-installed, use sync API
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("SMOKE_TEST_URL", "https://ganuda.us")
SCREENSHOT_DIR = os.environ.get("SCREENSHOT_DIR", "/ganuda/tests/screenshots")

PAGES = [
    {
        "path": "/index.html",
        "name": "Ops Console",
        "must_contain": ["Cherokee AI Federation"],
    },
    {
        "path": "/status.html",
        "name": "Status Page",
        "must_contain": ["Recently Completed"],
    },
    {
        "path": "/status-health.html",
        "name": "Health Page",
        "must_contain": [],  # may not exist yet
    },
    {
        "path": "/status-activity.html",
        "name": "Activity Page",
        "must_contain": [],
    },
]


def run_smoke_test(screenshot_all=False):
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    results = []
    start = time.monotonic()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-quic", "--disable-http2"]
        )
        context = browser.new_context(
            ignore_https_errors=True,
            user_agent="GanudaSmokeTest/1.0"
        )
        page = context.new_page()

        for test in PAGES:
            url = BASE_URL + test["path"]
            name = test["name"]
            t0 = time.monotonic()
            result = {
                "name": name,
                "url": url,
                "pass": True,
                "errors": [],
                "load_ms": 0,
                "headers": {},
            }

            try:
                # Capture response headers
                headers_captured = {}
                def on_response(response):
                    if response.url.rstrip("/") == url.rstrip("/") or response.url == url:
                        for k, v in response.headers.items():
                            headers_captured[k] = v
                page.on("response", on_response)

                resp = page.goto(url, wait_until="networkidle", timeout=15000)
                result["load_ms"] = round((time.monotonic() - t0) * 1000)
                result["headers"] = dict(headers_captured)
                result["status"] = resp.status if resp else 0

                # Check HTTP status
                if not resp or resp.status != 200:
                    if resp and resp.status == 404:
                        result["errors"].append(f"HTTP {resp.status} (page may not exist yet)")
                    else:
                        result["errors"].append(f"HTTP {resp.status if resp else 'no response'}")
                        result["pass"] = False

                # Check required content
                content = page.content()
                for text in test["must_contain"]:
                    if text not in content:
                        result["errors"].append(f"Missing: '{text}'")
                        result["pass"] = False

                # Check cache headers
                cc = headers_captured.get("cache-control", "")
                if "no-cache" not in cc and test["must_contain"]:
                    result["errors"].append(f"Missing Cache-Control: no-cache (got: '{cc}')")
                    result["pass"] = False

                alt_svc = headers_captured.get("alt-svc", "")
                if "h3" in alt_svc:
                    result["errors"].append(f"Alt-Svc still advertising h3: {alt_svc}")
                    result["pass"] = False

                # Screenshot on failure or if requested
                if not result["pass"] or screenshot_all:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_name = name.lower().replace(" ", "_")
                    ss_path = f"{SCREENSHOT_DIR}/{safe_name}_{ts}.png"
                    page.screenshot(path=ss_path, full_page=True)
                    result["screenshot"] = ss_path

                page.remove_listener("response", on_response)

            except Exception as e:
                result["pass"] = False
                result["errors"].append(str(e))
                result["load_ms"] = round((time.monotonic() - t0) * 1000)

            results.append(result)

        browser.close()

    total_ms = round((time.monotonic() - start) * 1000)

    # Report
    passed = sum(1 for r in results if r["pass"])
    failed = sum(1 for r in results if not r["pass"])
    warned = sum(1 for r in results if r["errors"] and r["pass"])

    print(f"\nGANUDA.US SMOKE TEST — {datetime.now().strftime('%Y-%m-%d %H:%M CT')}")
    print("=" * 60)

    for r in results:
        status = "PASS" if r["pass"] else "FAIL"
        if r["pass"] and r["errors"]:
            status = "WARN"
        load = f"{r['load_ms']}ms"
        print(f"  [{status}] {r['name']:<20} {load:>8}  {r['url']}")
        for e in r["errors"]:
            print(f"         ! {e}")
        if r.get("screenshot"):
            print(f"         > {r['screenshot']}")

    print(f"\nTotal: {passed} passed, {failed} failed, {warned} warned | {total_ms}ms")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smoke test ganuda.us with Playwright")
    parser.add_argument("--screenshot-all", action="store_true", help="Screenshot every page")
    args = parser.parse_args()
    sys.exit(run_smoke_test(screenshot_all=args.screenshot_all))
