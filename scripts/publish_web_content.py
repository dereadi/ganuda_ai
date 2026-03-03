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

try:
    from regenerate_blog_index import regenerate_blog_index
except ImportError:
    regenerate_blog_index = None

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

    # Auto-regenerate blog index when a blog post is published
    if not unpublish and url_path.startswith("/blog/") and url_path != "/blog/index.html":
        try:
            regenerate_blog_index()
            print("Blog index regenerated.")
        except Exception as e:
            print(f"Warning: blog index regeneration failed: {e}")
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