#!/usr/bin/env python3
"""
Regenerate blog index from HTML post files.

Scans /ganuda/www/ganuda.us/blog/*.html, extracts title/date/description
from HTML meta tags, sorts by date (newest first), generates index.html.

Called automatically by publish_web_content.py after each blog post publish.
Can also be run standalone: python3 regenerate_blog_index.py

Council Vote: #df0c89c957512c88 (tech debt sprint, Mar 3 2026)
"""

import os
import re
import hashlib
from datetime import datetime
from html.parser import HTMLParser

BLOG_DIR = "/ganuda/www/ganuda.us/blog"
INDEX_FILE = os.path.join(BLOG_DIR, "index.html")
WEB_ROOT = "/ganuda/www/ganuda.us"
SITE = "ganuda.us"

# DB config — same as publish_web_content.py
DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "dbname": "zammad_production",
    "user": "claude",
    "password": os.environ.get("CHEROKEE_DB_PASS", ""),
}


class MetaExtractor(HTMLParser):
    """Extract title, description, and date from blog post HTML."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.description = ""
        self.date_text = ""
        self._in_title = False
        self._in_meta = False
        self._in_date = False
        self._found_title = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "title" and not self._found_title:
            self._in_title = True
        if tag == "meta" and attrs_dict.get("name") == "description":
            self.description = attrs_dict.get("content", "")
        # Date is in <p class="article-meta"> or <div class="post-date">
        if tag == "p" and "article-meta" in attrs_dict.get("class", ""):
            self._in_date = True
        if tag == "div" and "post-date" in attrs_dict.get("class", ""):
            self._in_date = True

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_date and not self.date_text:
            self.date_text = data.strip()

    def handle_endtag(self, tag):
        if tag == "title" and self._in_title:
            self._in_title = False
            self._found_title = True
            # Strip " — Ganuda" or " - Ganuda" suffix
            self.title = re.sub(r"\s*[—\-]\s*Ganuda\s*$", "", self.title).strip()
        if tag in ("p", "div") and self._in_date:
            self._in_date = False


def parse_date_text(text):
    """Parse date text into a sortable datetime. Handles various formats."""
    # Strip author info: "March 2, 2026 · Derek Adair" -> "March 2, 2026"
    text = re.sub(r"\s*[·•|]\s*.*$", "", text).strip()

    # Try full date: "March 2, 2026"
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%B %d %Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass

    # Try month+year: "February 2026"
    for fmt in ("%B %Y", "%b %Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass

    # Try ISO: "2026-03-02"
    try:
        return datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        pass

    # Fallback: file modification time will be used
    return None


def scan_blog_posts():
    """Scan blog directory and extract metadata from each post."""
    posts = []
    for fname in os.listdir(BLOG_DIR):
        if not fname.endswith(".html") or fname == "index.html":
            continue

        fpath = os.path.join(BLOG_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue

        parser = MetaExtractor()
        parser.feed(content)

        # Parse date
        dt = parse_date_text(parser.date_text) if parser.date_text else None
        if dt is None:
            # Fallback to file mtime
            dt = datetime.fromtimestamp(os.path.getmtime(fpath))

        # Format display date
        if parser.date_text and re.match(r"^[A-Z][a-z]+ \d{4}$", parser.date_text.split("·")[0].strip()):
            display_date = parser.date_text.split("·")[0].strip()
        else:
            display_date = dt.strftime("%B %-d, %Y")

        posts.append({
            "filename": fname,
            "url_path": f"/blog/{fname}",
            "title": parser.title or fname.replace(".html", "").replace("-", " ").title(),
            "description": parser.description or "",
            "date": dt,
            "display_date": display_date,
        })

    # Sort newest first
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def generate_index_html(posts):
    """Generate blog index HTML matching the existing site design."""
    post_items = ""
    for p in posts:
        desc_html = f'<div class="post-desc">{p["description"]}</div>' if p["description"] else ""
        post_items += f"""
        <a href="{p['url_path']}" class="post-item">
            <div class="post-date">{p['display_date']}</div>
            <div class="post-title">{p['title']}</div>
            {desc_html}
            <div class="post-read">Read &rarr;</div>
        </a>
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blog — Ganuda</title>
    <meta name="description" content="Technical writing from the Cherokee AI Federation. Home lab AI, autonomous agents, veteran services, and living memory systems.">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{
            --navy: #1a365d;
            --charcoal: #2d3748;
            --gold: #d4a843;
            --teal: #4fd1c5;
            --warm: #f7fafc;
            --text: #e2e8f0;
            --muted: #a0aec0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--charcoal);
            color: var(--text);
            line-height: 1.8;
        }}
        a {{ color: var(--teal); text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .nav {{
            background: var(--navy);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--gold);
        }}
        .nav a {{ color: var(--muted); font-size: 0.9rem; }}
        .nav a:hover {{ color: var(--teal); text-decoration: none; }}
        .nav .brand {{ color: var(--gold); font-weight: 700; font-size: 1.1rem; letter-spacing: -0.5px; }}
        .page {{
            max-width: 740px;
            margin: 0 auto;
            padding: 4rem 2rem;
        }}
        .page h1 {{
            font-size: 2.4rem;
            line-height: 1.2;
            letter-spacing: -1px;
            color: white;
            margin-bottom: 0.5rem;
        }}
        .page-sub {{
            color: var(--muted);
            font-size: 1.1rem;
            font-style: italic;
            margin-bottom: 3rem;
            padding-bottom: 2rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .post-item {{
            display: block;
            padding: 2rem;
            margin-bottom: 1.5rem;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px;
            text-decoration: none;
            transition: transform 0.2s, border-color 0.2s;
        }}
        .post-item:hover {{
            transform: translateY(-2px);
            border-color: var(--gold);
            text-decoration: none;
        }}
        .post-date {{
            color: var(--gold);
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .post-title {{
            color: white;
            font-size: 1.4rem;
            font-weight: 700;
            margin: 0.5rem 0;
            line-height: 1.3;
        }}
        .post-desc {{
            color: var(--muted);
            font-size: 0.95rem;
            margin-bottom: 0.8rem;
        }}
        .post-read {{
            color: var(--teal);
            font-size: 0.9rem;
            font-weight: 600;
        }}
        .footer {{
            background: var(--navy);
            text-align: center;
            padding: 3rem 2rem;
            border-top: 2px solid var(--gold);
        }}
        .footer .cherokee {{
            font-size: 1.3rem;
            margin-bottom: 0.3rem;
            letter-spacing: 2px;
        }}
        .footer p {{
            color: var(--muted);
            font-size: 0.85rem;
        }}
        .footer .links {{ margin-top: 1rem; }}
        .footer .links a {{
            color: var(--muted);
            margin: 0 0.8rem;
            font-size: 0.85rem;
        }}
        .footer .links a:hover {{ color: var(--teal); }}
        @media (max-width: 600px) {{
            .page h1 {{ font-size: 1.8rem; }}
            .page {{ padding: 2rem 1.5rem; }}
            .post-title {{ font-size: 1.2rem; }}
        }}
    </style>
</head>
<body>

    <div class="nav">
        <a href="/" class="brand">Ganuda</a>
        <div>
            <a href="/">Home</a>
        </div>
    </div>

    <div class="page">

        <h1>Blog</h1>
        <p class="page-sub">Technical writing from the Cherokee AI Federation</p>
{post_items}
    </div>

    <div class="footer">
        <div class="cherokee">&#x13E3;&#x13B3;&#x13A9; &#x13D7;&#x13C2;&#x13F8;&#x13B5;</div>
        <p>Cherokee AI Federation</p>
        <p style="margin-top: 0.3rem;">For Seven Generations</p>
        <div class="links">
            <a href="/">Home</a>
            <a href="https://vetassist.ganuda.us">VetAssist</a>
            <a href="mailto:hello@ganuda.us">Contact</a>
        </div>
        <p style="margin-top: 1.5rem; font-size: 0.75rem;">&copy; 2025-2026 Ganuda</p>
    </div>

</body>
</html>
"""


def publish_index(html_content):
    """Publish generated index to web_content table and write to disk."""
    # Write to disk
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Wrote {INDEX_FILE} ({len(html_content)} bytes)")

    # Publish to web_content table for materializer
    try:
        import psycopg2
        content_hash = hashlib.sha256(html_content.encode("utf-8")).hexdigest()
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO web_content (site, path, content_type, content, content_hash, created_by)
            VALUES (%s, '/blog/index.html', 'text/html', %s, %s, 'blog_index_generator')
            ON CONFLICT (site, path) DO UPDATE SET
                content = EXCLUDED.content,
                content_hash = EXCLUDED.content_hash,
                updated_at = NOW()
        """, (SITE, html_content, content_hash))
        conn.commit()
        cur.close()
        conn.close()
        print("Published to web_content table.")
    except Exception as e:
        print(f"Warning: web_content publish failed (index still written to disk): {e}")


def regenerate_blog_index():
    """Main entry point. Scan posts, generate index, publish."""
    posts = scan_blog_posts()
    if not posts:
        print("No blog posts found — skipping index regeneration.")
        return False

    html = generate_index_html(posts)
    publish_index(html)
    print(f"Blog index regenerated with {len(posts)} post(s).")
    return True


if __name__ == "__main__":
    regenerate_blog_index()