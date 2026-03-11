# [RECURSIVE] Status Page: Unified Organism Activity Timeline - Step 5

**Parent Task**: #1208
**Auto-decomposed**: 2026-03-10T07:20:17.121919
**Original Step Title**: Wire into status page

---

### Step 5: Wire into status page

The existing status page at ganuda.us/status.html needs to include this timeline fragment. Either:
- Option A: Modify the status page generator to fetch and embed the `/status-activity.html` content
- Option B: Use JavaScript `fetch('/status-activity.html')` to load the timeline dynamically
- Option C: Have the materializer on owlfin/eaglefin compose the final page from fragments

Choose the approach that fits the existing materializer pattern. The timeline publishes as a separate web_content entry at `/status-activity.html` so it can be updated independently (every 15 minutes via timer) without rebuilding the full status page.
