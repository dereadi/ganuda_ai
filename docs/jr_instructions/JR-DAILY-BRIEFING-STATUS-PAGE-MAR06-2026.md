# Jr Instruction: Daily Briefing → Status Page Integration

**Task**: Wire DailyBriefingGenerator output to web_content so Chief can see it at ganuda.us/briefing.html
**Priority**: 3
**Story Points**: 3
**Epic**: #1958

## Context

`/ganuda/services/chief_pa/daily_briefing.py` generates a morning briefing but currently only routes to Slack. We need it to also publish an HTML version to `web_content` (like `generate_status_page.py` does).

The `web_content` table has columns: `site`, `path`, `content`, `content_type`, `content_hash`, `published`, `updated_at`. Unique constraint on `(site, path)`.

## Steps

### Step 1: Add publish_to_web method to DailyBriefingGenerator

File: `/ganuda/services/chief_pa/daily_briefing.py`

```
<<<<<<< SEARCH
class DailyBriefingGenerator:
    """Assembles and delivers the Chief's morning briefing.

    Usage:
        generator = DailyBriefingGenerator(config)
        generator.generate_and_send()

    The briefing has five sections:
=======
class DailyBriefingGenerator:
    """Assembles and delivers the Chief's morning briefing.

    Usage:
        generator = DailyBriefingGenerator(config)
        generator.generate_and_send()
        generator.publish_to_web()  # Also publishes HTML to ganuda.us/briefing.html

    The briefing has five sections:
>>>>>>> REPLACE
```

### Step 2: Add the publish_to_web method

Add this method to the DailyBriefingGenerator class, after the existing `generate_and_send` method:

File: `/ganuda/services/chief_pa/daily_briefing.py`

```
<<<<<<< SEARCH
    def _build_fallback_briefing(self):
=======
    def publish_to_web(self, briefing_text: str):
        """Publish briefing as HTML to web_content for ganuda.us/briefing.html."""
        import hashlib
        if not DB_AVAILABLE:
            logger.warning("Cannot publish to web: psycopg2 unavailable")
            return

        now = datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M CT")
        sections = briefing_text.split("\n\n")
        sections_html = ""
        for section in sections:
            lines = section.strip().split("\n")
            if not lines:
                continue
            header = lines[0].strip().lstrip("#").strip()
            body = "<br>".join(lines[1:]) if len(lines) > 1 else ""
            sections_html += f'<div class="card"><h2>{header}</h2><div class="body">{body}</div></div>\n'

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Daily Briefing</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: -apple-system, system-ui, sans-serif; background:#0a0e14; color:#c8ccd4; padding:16px; max-width:600px; margin:0 auto; }}
  h1 {{ font-size:1.3em; color:#e8b04a; margin-bottom:4px; }}
  .subtitle {{ font-size:0.8em; color:#666; margin-bottom:16px; }}
  .card {{ background:#151a22; border-radius:8px; padding:12px; margin-bottom:12px; }}
  .card h2 {{ font-size:0.95em; color:#7aafff; margin-bottom:8px; }}
  .body {{ font-size:0.85em; line-height:1.5; }}
</style>
</head>
<body>
<h1>Daily Briefing</h1>
<div class="subtitle">Generated: {now}</div>
{sections_html}
<div style="text-align:center; margin-top:16px; font-size:0.7em; color:#444;">
  For Seven Generations
</div>
</body>
</html>"""

        content_hash = hashlib.sha256(html.encode()).hexdigest()
        db_config = self.config.get("database", {})
        conn = psycopg2.connect(
            host=db_config.get("host", os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")),
            port=5432,
            dbname=db_config.get("name", os.environ.get("CHEROKEE_DB_NAME", "zammad_production")),
            user=db_config.get("user", os.environ.get("CHEROKEE_DB_USER", "claude")),
            password=db_config.get("password", os.environ.get("CHEROKEE_DB_PASS", ""))
        )
        cur = conn.cursor()
        cur.execute("""INSERT INTO web_content (site, path, content, content_type, content_hash, published, updated_at)
            VALUES ('ganuda.us', '/briefing.html', %s, 'text/html', %s, true, NOW())
            ON CONFLICT (site, path) DO UPDATE SET content = %s, content_hash = %s, updated_at = NOW()""",
            (html, content_hash, html, content_hash))
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Briefing published to web_content /briefing.html")

    def _build_fallback_briefing(self):
>>>>>>> REPLACE
```

## Verification

1. Import check: `python3 -c "from services.chief_pa.daily_briefing import DailyBriefingGenerator; print('OK')"`
2. Method exists: `python3 -c "from services.chief_pa.daily_briefing import DailyBriefingGenerator; assert hasattr(DailyBriefingGenerator, 'publish_to_web'); print('publish_to_web exists')"`
