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