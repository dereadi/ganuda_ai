# Jr Instruction: Ops Console Quick Links Grid

**Task**: Add a quick-links homepage to ganuda.us with links to key internal pages
**Priority**: 3
**Story Points**: 3
**Epic**: #1974

## Context

ganuda.us currently has a blog index and status page. We need a proper homepage (`/index.html`) that serves as an internal ops switchboard. The existing `/index.html` in web_content should be replaced with a quick-links grid.

Publish by inserting/updating into `web_content` table on bluefin (192.168.132.222, db=zammad_production, user=claude). The materializer on owlfin/eaglefin will pick it up.

## Steps

### Step 1: Create the ops console homepage generator

Create `/ganuda/scripts/generate_ops_console.py`

```python
#!/usr/bin/env python3
"""Generate the Ops Console homepage for ganuda.us."""

import psycopg2
import os
import hashlib
from datetime import datetime

DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")


def generate():
    now = datetime.now().strftime("%Y-%m-%d %H:%M CT")

    links = [
        ("Status", "/status.html", "#4a7", "Live cluster vitals, Jr tasks, kanban"),
        ("Briefing", "/briefing.html", "#7af", "Daily morning briefing from Chief PA"),
        ("Blog", "/blog/index.html", "#fa7", "Federation technical blog"),
        ("Photos", "/photos.html", "#a7f", "Cherokee Nation + Federation gallery"),
        ("LLMs.txt", "/llms.txt", "#888", "Machine-readable federation manifest"),
    ]

    grid_html = ""
    for name, href, color, desc in links:
        grid_html += f'''<a href="{href}" class="link-card" style="border-left:4px solid {color}">
  <div class="link-name">{name}</div>
  <div class="link-desc">{desc}</div>
</a>\n'''

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cherokee AI Federation</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: -apple-system, system-ui, sans-serif; background:#0a0e14; color:#c8ccd4; padding:16px; max-width:600px; margin:0 auto; }}
  h1 {{ font-size:1.4em; color:#e8b04a; margin-bottom:4px; }}
  .subtitle {{ font-size:0.8em; color:#666; margin-bottom:20px; }}
  .link-card {{ display:block; background:#151a22; border-radius:8px; padding:14px; margin-bottom:10px; text-decoration:none; color:#c8ccd4; transition:background 0.2s; }}
  .link-card:hover {{ background:#1a2030; }}
  .link-name {{ font-size:1.1em; font-weight:600; color:#7aafff; margin-bottom:4px; }}
  .link-desc {{ font-size:0.8em; color:#888; }}
  .footer {{ text-align:center; margin-top:24px; font-size:0.7em; color:#444; }}
</style>
</head>
<body>
<h1>Cherokee AI Federation</h1>
<div class="subtitle">Ops Console &mdash; {now}</div>
{grid_html}
<div class="footer">For Seven Generations &mdash; DC-1 through DC-11</div>
</body>
</html>"""

    content_hash = hashlib.sha256(html.encode()).hexdigest()
    conn = psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    cur.execute("""INSERT INTO web_content (site, path, content, content_type, content_hash, published, updated_at)
        VALUES ('ganuda.us', '/index.html', %s, 'text/html', %s, true, NOW())
        ON CONFLICT (site, path) DO UPDATE SET content = %s, content_hash = %s, updated_at = NOW()""",
        (html, content_hash, html, content_hash))
    conn.commit()
    cur.close()
    conn.close()
    print(f"Ops console published ({len(html)} bytes)")


if __name__ == "__main__":
    if not DB_PASS:
        import re
        try:
            with open("/ganuda/config/secrets.env") as f:
                for line in f:
                    m = re.match(r"^(\w+)=(.+)$", line.strip())
                    if m:
                        os.environ[m.group(1)] = m.group(2)
            DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")
        except FileNotFoundError:
            pass
    generate()
```

## Verification

1. Run: `cd /ganuda && python3 scripts/generate_ops_console.py`
2. Check: `curl -s https://ganuda.us/index.html | head -5` should show the new page
