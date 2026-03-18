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
        conn.commit()  # explicit commit before close
        conn.close()

        if updated > 0:
            log.info("Materialized %d file(s)", updated)
        return True

    except psycopg2.OperationalError as e:
        log.warning("DB unreachable, serving stale cache: %s", e)
        if conn:
            try:
                conn.commit()  # explicit commit before close
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