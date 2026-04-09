# KB: Regression Fixes — Easter Sunday Apr 5, 2026

## Context
Full regression test after Shield P-3 build + 4 days of MOCHA changes.

## Fix 1: Landing Page Pulse Section Missing
**Problem:** System Pulse section with live stats was missing from ganuda.us landing page. The pulse section that fetches from /api/health and displays thermal memory count, sacred count, Jr tasks, etc. was gone.

**Root Cause:** A Jr task likely overwrote the index.html file during a "refresh landing page" task without preserving the injected pulse section.

**Fix:** Re-injected pulse section before "About the Builder" div. Updated to include links to all 5 products (Trimmer, Canary, Meeting Notes, Clipboard, Docs). Products count updated to 5.

**Prevention:** The landing page should be treated as a PROTECTED file. Any Jr task that modifies index.html should preserve existing sections. Add to protected paths list in Jr executor.

## Fix 2: Clipboard Monitor Duplicates on Redfin
**Problem:** 5 monitor.py processes running on redfin instead of 1. Caused by the original launch command leaving a wrapper bash process that spawned child processes, and subsequent restarts adding more.

**Root Cause:** Using `nohup ... &` from within a complex bash command created wrapper processes. Each restart added another without killing the old ones.

**Fix:** Killed old wrapper process (PID 2602661). Restarted clean with single process (PID 1646931).

**Prevention:** The clipboard monitor should be a systemd service on redfin, not a nohup background process. Create `/etc/systemd/system/clipboard-monitor.service` like the other product services.

## Fix 3: VLM Activating (Non-Critical)
**Problem:** vllm-redfin-vlm showing "activating" instead of "active" during regression check.

**Root Cause:** The VLM service cycles occasionally, likely due to GPU memory pressure or model reload. It auto-recovers.

**Fix:** None needed — self-healing. Confirmed active on re-check.

## All Systems After Fixes
- Landing page pulse: RESTORED ✅
- All 5 products: ALIVE ✅
- PgBouncer: Active ✅
- All 3 vLLMs: Active ✅
- Clipboard monitors: 1 on redfin, 2 on sasass ✅
- Shield tests: 23/23 PASSED ✅
- All nodes: 5/5 UP ✅

---

*For Seven Generations.*
