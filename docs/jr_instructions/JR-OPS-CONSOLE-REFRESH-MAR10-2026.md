# Jr Instruction: Ops Console Refresh — Add Health + Activity Links, Update Footer

**Task #1236**
**Date:** 2026-03-10
**Priority:** 1 (External visitors may be looking at ganuda.us TODAY)
**TPM:** Claude Opus

## Context

The ops console at ganuda.us/index.html is the landing page for the Cherokee AI Federation. It currently links to Status, Briefing, Blog, Photos, and LLMs.txt. Two new pages exist that aren't linked: the Node Health dashboard (/health.html) and the Activity Timeline (/status-activity.html). The footer also references "DC-1 through DC-11" but we're now at DC-16. External visitors (potential employers, collaborators) may be viewing this page today.

## Task

Update `/ganuda/scripts/generate_ops_console.py` to add two new link cards and update the footer, then republish the ops console.

## Steps

### Step 1: Edit the links array in generate_ops_console.py

Open `/ganuda/scripts/generate_ops_console.py` and find the `links` list.

<<<<<<< SEARCH
    links = [
        ("Status", "/status.html", "#4a7", "Live cluster vitals, Jr tasks, kanban"),
        ("Briefing", "/briefing.html", "#7af", "Daily morning briefing from Chief PA"),
        ("Blog", "/blog/index.html", "#fa7", "Federation technical blog"),
        ("Photos", "/photos.html", "#a7f", "Cherokee Nation + Federation gallery"),
        ("LLMs.txt", "/llms.txt", "#888", "Machine-readable federation manifest"),
    ]
=======
    links = [
        ("Status", "/status.html", "#4a7", "Live cluster vitals, Jr tasks, kanban"),
        ("Health", "/health.html", "#f55", "Node health dashboard across all 6 nodes"),
        ("Activity", "/status-activity.html", "#5d5", "Real-time organism activity timeline"),
        ("Briefing", "/briefing.html", "#7af", "Daily morning briefing from Chief PA"),
        ("Blog", "/blog/index.html", "#fa7", "Federation technical blog"),
        ("Photos", "/photos.html", "#a7f", "Cherokee Nation + Federation gallery"),
        ("LLMs.txt", "/llms.txt", "#888", "Machine-readable federation manifest"),
    ]
>>>>>>> REPLACE

### Step 2: Update the footer design constraint reference

In the same file, find the footer line.

<<<<<<< SEARCH
<div class="footer">For Seven Generations &mdash; DC-1 through DC-11</div>
=======
<div class="footer">For Seven Generations &mdash; DC-1 through DC-16</div>
>>>>>>> REPLACE

### Step 3: Republish the ops console

Run the generator to publish the updated page:

```bash
cd /ganuda && python3 scripts/generate_ops_console.py
```

Expected output: `Ops console published (XXXX bytes)`

### Step 4: Verify materialization

Wait 30 seconds for the DMZ materializer to pick up the change, then verify:

```bash
curl -s https://ganuda.us/ | grep -o 'Health\|Activity\|DC-16'
```

Expected: All three strings should appear in the output.

## Acceptance Criteria

- `/ganuda/scripts/generate_ops_console.py` has 7 link cards (was 5)
- Health link points to `/health.html` with red accent color
- Activity link points to `/status-activity.html` with green accent color
- Footer reads "DC-1 through DC-16"
- `python3 scripts/generate_ops_console.py` runs without error and publishes to web_content
- Page is visible at ganuda.us within 60 seconds of publish

## Constraints

- Do NOT change the page layout, styling, or structure beyond adding cards and updating footer
- Do NOT modify any other scripts
- Do NOT remove existing link cards
- Keep the same card ordering logic: operational pages first, content pages second, machine-readable last
