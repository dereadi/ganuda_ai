# JR Instruction: Blog Index Auto-Regeneration

**Task ID**: BLOG-INDEX-AUTOREGEN
**Priority**: 3
**Assigned Jr**: Software Engineer Jr.
**Sacred Fire**: false
**Use RLM**: false
**TEG Plan**: true

## Context

The blog index at `/blog/index.html` on ganuda.us is a manually maintained HTML file stored in the `web_content` table. When new blog posts are published via `publish_web_content.py`, the index is NOT updated — the new post is invisible from the blog listing page. This is Deer's (PR/content pipeline) responsibility to keep current automatically.

## Objective

Create a `regenerate_blog_index.py` script that rebuilds the blog index from the database, and wire it into the publish flow so it fires automatically after any blog post publish.

## Architecture

- **Database**: `web_content` table on bluefin (192.168.132.222:5432, db: zammad_production, user: claude)
- **Blog posts**: rows where `path LIKE '/blog/%.html' AND path != '/blog/index.html' AND published = true`
- **Blog index**: row where `path = '/blog/index.html'`
- **Materializer**: polls web_content every 30s and writes to DMZ nodes (owlfin/eaglefin)
- **Publish script**: `/ganuda/scripts/publish_web_content.py`

## Step 1: Create regenerate_blog_index.py

Create `/ganuda/scripts/regenerate_blog_index.py`

The script must:

1. Query all published blog posts from `web_content` (excluding `/blog/index.html`)
2. For each post, extract metadata from the HTML content:
   - **Title**: from `<title>` tag (strip any " — Ganuda" suffix)
   - **Date**: from the first element with class `post-date` or `date` in the HTML. Use regex: `class="(?:post-date|date)"[^>]*>([^<]+)<`
   - **Description**: from `<meta name="description" content="...">` tag
3. Sort posts by date descending (parse dates with `dateutil.parser` or manual parsing — most dates are like "March 1, 2026" or "February 2026")
4. Build the index HTML using the EXACT template structure from the current index (nav, styling, footer — all preserved). The only dynamic part is the `<a class="post-item">` blocks in the `.page` div.
5. Compute sha256 hash of the generated HTML
6. Upsert into `web_content` table (site='ganuda.us', path='/blog/index.html')
7. Print summary: how many posts indexed, any posts with missing metadata

### Template for each post-item block:

```text
        <a href="{path}" class="post-item">
            <div class="post-date">{date}</div>
            <div class="post-title">{title}</div>
            <div class="post-desc">{description}</div>
            <div class="post-read">Read &rarr;</div>
        </a>
```

### The full HTML template (header, CSS, nav, footer) should be extracted from the CURRENT `/blog/index.html` row in web_content — split on the first `<a href=` with class `post-item` and the last `</a>` before the footer. This way if the design changes, the index generator picks it up.

Simpler approach: hardcode the template prefix (everything before the post items) and suffix (everything after) as string constants in the script, copied from the current index.html. This is fine — the design doesn't change often.

### DB connection pattern (match existing scripts):

```python
import os
import psycopg2

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "dbname": "zammad_production",
    "user": "claude",
    "password": os.environ.get("CHEROKEE_DB_PASS", ""),
}
```

### Can be run standalone:

```text
python3 /ganuda/scripts/regenerate_blog_index.py
```

## Step 2: Wire into publish_web_content.py

File: `/ganuda/scripts/publish_web_content.py`

After the publish upsert succeeds (line 69, after the print), add a check: if the published path starts with `/blog/` and is not `/blog/index.html`, call `regenerate_blog_index()`.

Import the function from the new script:

```text
<<<<<<< SEARCH
import psycopg2
=======
import psycopg2

from regenerate_blog_index import regenerate_blog_index
>>>>>>> REPLACE
```

Then after the publish print:

```text
<<<<<<< SEARCH
        print(f"Published: {url_path} ({len(content)} bytes)")

    conn.commit()
=======
        print(f"Published: {url_path} ({len(content)} bytes)")

    conn.commit()

    # Auto-regenerate blog index when a blog post is published
    if not unpublish and url_path.startswith("/blog/") and url_path != "/blog/index.html":
        try:
            regenerate_blog_index()
            print("Blog index regenerated.")
        except Exception as e:
            print(f"Warning: blog index regeneration failed: {e}")
>>>>>>> REPLACE
```

Note: The import needs to work from the scripts directory. Since both files are in `/ganuda/scripts/`, a simple import works. If not, use:

```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

## Step 3: Populate metadata jsonb (optional enhancement)

After extracting title/date/description from each post, also update the `metadata` jsonb column on each blog post row so future queries don't need to re-parse HTML:

```sql
UPDATE web_content SET metadata = jsonb_build_object(
    'title', %s, 'date', %s, 'description', %s, 'type', 'blog_post'
) WHERE site = 'ganuda.us' AND path = %s AND (metadata = '{}' OR metadata IS NULL);
```

This is a one-time backfill that happens during index generation. Once metadata is populated, the script can prefer metadata over HTML parsing.

## Verification

1. Run `python3 /ganuda/scripts/regenerate_blog_index.py` — should print all 10 blog posts found and "Blog index updated"
2. Check DB: `SELECT length(content), content_hash FROM web_content WHERE path='/blog/index.html';` — should show new hash
3. Wait 30s for materializer, then `curl -s https://ganuda.us/blog/ | grep "natural-falls"` — should find the Natural Falls post
4. Publish a test: verify the index auto-regenerates

## Files Modified

- Create: `/ganuda/scripts/regenerate_blog_index.py`
- Modify: `/ganuda/scripts/publish_web_content.py` (add auto-regen call)
