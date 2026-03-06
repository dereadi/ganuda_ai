# JR INSTRUCTION: Web Content Postgres + File Cache System

**Task ID**: WEB-CONTENT-001
**Priority**: 3
**Assigned Jr**: Software Engineer Jr.
**Sacred Fire Priority**: false
**TEG Plan**: false
**use_rlm**: false

## Context

Council vote #b875a756efe895d0 (0.793 confidence, PROCEED WITH CAUTION) selected Option B: Postgres + File Cache for serving web content on DMZ nodes owlfin/eaglefin.

**Current state**: Static HTML/CSS/JS lives on redfin at `/ganuda/www/ganuda.us/`. Owlfin/eaglefin serve via Caddy `file_server` from `/home/dereadi/www/ganuda.us/`. Content is manually rsync'd — this drifts, breaks, and creates 404s.

**Target state**: Content stored in Postgres (bluefin). A lightweight materializer daemon on owlfin/eaglefin polls for changes and writes files to the Caddy web root. Caddy config unchanged — it keeps serving static files.

## Step 1: Database Schema (runs on bluefin via psql)

Create the `web_content` table on bluefin (192.168.132.222).

Create `/ganuda/scripts/migrations/web_content_schema.sql`:

```python
"""
Web Content Schema Migration
Creates the web_content table for Postgres + File Cache web serving.
Run: psql -h 192.168.132.222 -U claude -d zammad_production -f /ganuda/scripts/migrations/web_content_schema.sql
"""
```

File: `/ganuda/scripts/migrations/web_content_schema.sql`
```text
-- Web Content: Postgres + File Cache (Council vote #b875a756efe895d0)
-- Content stored in DB, materialized to disk on DMZ nodes by daemon

CREATE TABLE IF NOT EXISTS web_content (
    id SERIAL PRIMARY KEY,
    site VARCHAR(100) NOT NULL DEFAULT 'ganuda.us',
    path VARCHAR(500) NOT NULL,
    content_type VARCHAR(50) NOT NULL DEFAULT 'text/html',
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    metadata JSONB DEFAULT '{}',
    published BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100) DEFAULT 'tpm'
);

-- Unique constraint: one content per site+path
CREATE UNIQUE INDEX IF NOT EXISTS idx_web_content_site_path
    ON web_content (site, path);

-- Index for materializer polling
CREATE INDEX IF NOT EXISTS idx_web_content_updated
    ON web_content (updated_at);

-- Index for published content only
CREATE INDEX IF NOT EXISTS idx_web_content_published
    ON web_content (site, published) WHERE published = true;

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_web_content_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    NEW.content_hash = encode(digest(NEW.content, 'sha256'), 'hex');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_web_content_updated ON web_content;
CREATE TRIGGER trg_web_content_updated
    BEFORE UPDATE ON web_content
    FOR EACH ROW
    EXECUTE FUNCTION update_web_content_timestamp();
```

## Step 2: Content Seeder Script

Create `/ganuda/scripts/seed_web_content.py` — reads existing HTML files from `/ganuda/www/ganuda.us/` and inserts them into the `web_content` table.

File: `/ganuda/scripts/seed_web_content.py`
```python
#!/usr/bin/env python3
"""Seed web_content table from existing static files on redfin."""

import os
import hashlib
import psycopg2

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "dbname": "zammad_production",
    "user": "claude",
    "password": os.environ.get("CHEROKEE_DB_PASS", ""),
}

WEB_ROOT = "/ganuda/www/ganuda.us"
SITE = "ganuda.us"


def seed():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    count = 0

    for root, dirs, files in os.walk(WEB_ROOT):
        for fname in files:
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, WEB_ROOT)
            # Normalize to URL path with leading slash
            url_path = "/" + rel_path

            # Determine content type
            ext = os.path.splitext(fname)[1].lower()
            content_types = {
                ".html": "text/html",
                ".css": "text/css",
                ".js": "application/javascript",
                ".json": "application/json",
                ".md": "text/markdown",
                ".xml": "text/xml",
                ".txt": "text/plain",
                ".svg": "image/svg+xml",
            }
            content_type = content_types.get(ext)
            if content_type is None:
                print(f"  SKIP (binary/unknown): {rel_path}")
                continue

            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

            cur.execute(
                """
                INSERT INTO web_content (site, path, content_type, content, content_hash, created_by)
                VALUES (%s, %s, %s, %s, %s, 'seeder')
                ON CONFLICT (site, path) DO UPDATE SET
                    content = EXCLUDED.content,
                    content_hash = EXCLUDED.content_hash,
                    content_type = EXCLUDED.content_type,
                    updated_at = NOW()
                """,
                (SITE, url_path, content_type, content, content_hash),
            )
            count += 1
            print(f"  UPSERT: {url_path} ({len(content)} bytes)")

    conn.commit()
    cur.close()
    conn.close()
    print(f"\nSeeded {count} files into web_content for site '{SITE}'")


if __name__ == "__main__":
    seed()
```

## Step 3: Materializer Daemon

Create `/ganuda/services/web_materializer.py` — runs on owlfin/eaglefin. Polls Postgres every 30 seconds for changes, writes updated files to the Caddy web root.

File: `/ganuda/services/web_materializer.py`
```python
#!/usr/bin/env python3
"""
Web Content Materializer — Postgres to File Cache

Runs on DMZ nodes (owlfin/eaglefin). Polls web_content table for changes
and writes files to the Caddy web root. If DB is unreachable, stale cache
continues serving.

Council vote #b875a756efe895d0 — Option B: Postgres + File Cache
"""

import os
import sys
import time
import hashlib
import signal
import logging

import psycopg2
import psycopg2.extras

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "dbname": "zammad_production",
    "user": "claude",
    "password": os.environ.get("CHEROKEE_DB_PASS", ""),
}

SITE = "ganuda.us"
WEB_ROOT = "/home/dereadi/www/ganuda.us"
POLL_INTERVAL = 30  # seconds
HASH_CACHE_FILE = os.path.join(WEB_ROOT, ".materializer_hashes.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [materializer] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

running = True


def signal_handler(signum, frame):
    global running
    log.info("Received signal %d, shutting down", signum)
    running = False


signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


def load_local_hashes():
    """Build hash map of existing files on disk."""
    hashes = {}
    for root, dirs, files in os.walk(WEB_ROOT):
        for fname in files:
            if fname.startswith("."):
                continue
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, WEB_ROOT)
            url_path = "/" + rel_path
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                hashes[url_path] = hashlib.sha256(content.encode("utf-8")).hexdigest()
            except (UnicodeDecodeError, IOError):
                pass  # skip binary files
    return hashes


def materialize():
    """Poll DB and write changed files."""
    local_hashes = load_local_hashes()
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute(
            "SELECT path, content, content_hash FROM web_content "
            "WHERE site = %s AND published = true",
            (SITE,),
        )

        db_paths = set()
        updated = 0
        for row in cur.fetchall():
            path = row["path"]
            db_paths.add(path)
            db_hash = row["content_hash"]

            if local_hashes.get(path) == db_hash:
                continue  # no change

            # Write file
            file_path = os.path.join(WEB_ROOT, path.lstrip("/"))
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(row["content"])
            updated += 1
            log.info("Updated: %s (%d bytes)", path, len(row["content"]))

        # Remove files that were unpublished/deleted from DB
        for local_path in list(local_hashes.keys()):
            if local_path not in db_paths:
                file_path = os.path.join(WEB_ROOT, local_path.lstrip("/"))
                if os.path.exists(file_path):
                    os.remove(file_path)
                    log.info("Removed (unpublished): %s", local_path)

        cur.close()
        conn.close()

        if updated > 0:
            log.info("Materialized %d file(s)", updated)
        return True

    except psycopg2.OperationalError as e:
        log.warning("DB unreachable, serving stale cache: %s", e)
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        return False


def main():
    log.info("Starting web materializer for site '%s'", SITE)
    log.info("Web root: %s", WEB_ROOT)
    log.info("Poll interval: %ds", POLL_INTERVAL)

    # Initial sync
    materialize()

    while running:
        time.sleep(POLL_INTERVAL)
        if running:
            materialize()

    log.info("Materializer stopped")


if __name__ == "__main__":
    main()
```

## Step 4: Content Publisher Utility

Create `/ganuda/scripts/publish_web_content.py` — convenience script for publishing new content from redfin.

File: `/ganuda/scripts/publish_web_content.py`
```python
#!/usr/bin/env python3
"""
Publish a file to web_content table.

Usage:
    python3 publish_web_content.py /ganuda/www/ganuda.us/blog/my-post.html
    python3 publish_web_content.py /ganuda/www/ganuda.us/blog/my-post.html --unpublish
"""

import os
import sys
import hashlib
import argparse

import psycopg2

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "dbname": "zammad_production",
    "user": "claude",
    "password": os.environ.get("CHEROKEE_DB_PASS", ""),
}

WEB_ROOT = "/ganuda/www/ganuda.us"
SITE = "ganuda.us"


def publish(file_path, unpublish=False):
    rel_path = os.path.relpath(file_path, WEB_ROOT)
    url_path = "/" + rel_path

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    if unpublish:
        cur.execute(
            "UPDATE web_content SET published = false WHERE site = %s AND path = %s",
            (SITE, url_path),
        )
        print(f"Unpublished: {url_path}")
    else:
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            ".html": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".md": "text/markdown",
        }
        content_type = content_types.get(ext, "text/plain")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        cur.execute(
            """
            INSERT INTO web_content (site, path, content_type, content, content_hash, created_by)
            VALUES (%s, %s, %s, %s, %s, 'publisher')
            ON CONFLICT (site, path) DO UPDATE SET
                content = EXCLUDED.content,
                content_hash = EXCLUDED.content_hash,
                content_type = EXCLUDED.content_type,
                updated_at = NOW()
            """,
            (SITE, url_path, content_type, content, content_hash),
        )
        print(f"Published: {url_path} ({len(content)} bytes)")

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publish web content to Postgres")
    parser.add_argument("file", help="Path to file to publish")
    parser.add_argument("--unpublish", action="store_true", help="Unpublish content")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"File not found: {args.file}")
        sys.exit(1)

    publish(args.file, args.unpublish)
```

## Deployment Notes (TPM / Chief — requires sudo)

### Systemd service for materializer (owlfin + eaglefin):

Create `/etc/systemd/system/web-materializer.service` on both DMZ nodes:

```text
[Unit]
Description=Web Content Materializer (Postgres → File Cache)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=dereadi
Environment=CHEROKEE_DB_PASS=<password>
ExecStart=/usr/bin/python3 /ganuda/services/web_materializer.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```text
sudo systemctl daemon-reload
sudo systemctl enable web-materializer
sudo systemctl start web-materializer
```

### Prerequisite: psycopg2 on owlfin/eaglefin

```text
pip3 install psycopg2-binary
```

### Migration order:
1. Run schema SQL on bluefin
2. Run seeder on redfin to populate table
3. Deploy materializer + service on owlfin and eaglefin
4. Verify content appears, then remove manual rsync workflow
