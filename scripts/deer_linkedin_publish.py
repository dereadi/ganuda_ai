#!/usr/bin/env python3
"""Deer LinkedIn Publisher — publishes approved drafts via Late.dev API."""

import json
import os
import re
import requests
import psycopg2
from datetime import datetime


DB_HOST = os.environ.get("CHEROKEE_DB_HOST", os.environ.get('CHEROKEE_DB_HOST', '10.100.0.2'))
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")
LATE_API_KEY = os.environ.get("LATE_DEV_API_KEY", "")
LATE_ACCOUNT_ID = os.environ.get("LATE_DEV_LINKEDIN_ACCOUNT_ID", "")
LATE_API_URL = "https://getlate.dev/api/v1/posts"


def load_secrets():
    global DB_PASS, LATE_API_KEY, LATE_ACCOUNT_ID
    if not DB_PASS or not LATE_API_KEY:
        try:
            with open("/ganuda/config/secrets.env") as f:
                for line in f:
                    m = re.match(r"^(\w+)=(.+)$", line.strip())
                    if m:
                        os.environ[m.group(1)] = m.group(2)
            DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")
            LATE_API_KEY = os.environ.get("LATE_DEV_API_KEY", "")
            LATE_ACCOUNT_ID = os.environ.get("LATE_DEV_LINKEDIN_ACCOUNT_ID", "")
        except FileNotFoundError:
            pass


def publish_to_linkedin(content):
    """Publish a post via Late.dev API."""
    resp = requests.post(LATE_API_URL, headers={
        "Authorization": f"Bearer {LATE_API_KEY}",
        "Content-Type": "application/json",
    }, json={
        "content": content,
        "platforms": [{"platform": "linkedin", "accountId": LATE_ACCOUNT_ID}],
        "publishNow": True,
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main():
    load_secrets()
    if not LATE_API_KEY or not LATE_ACCOUNT_ID:
        print("ERROR: LATE_DEV_API_KEY or LATE_DEV_LINKEDIN_ACCOUNT_ID not set in secrets.env")
        return

    conn = psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()

    cur.execute("""SELECT id, draft_content FROM linkedin_drafts
        WHERE status = 'approved' ORDER BY id LIMIT 1""")
    row = cur.fetchone()
    if not row:
        print("No approved drafts to publish")
        cur.close()
        conn.commit()  # explicit commit before close
        conn.close()
        return

    draft_id, content = row
    print(f"Publishing draft #{draft_id} ({len(content)} chars)...")

    try:
        result = publish_to_linkedin(content)
        post_id = result.get("id", result.get("postId", "unknown"))
        cur.execute("""UPDATE linkedin_drafts
            SET status = 'published', published_at = NOW(), late_dev_post_id = %s
            WHERE id = %s""", (str(post_id), draft_id))
        conn.commit()
        print(f"Published! Late.dev post ID: {post_id}")
    except requests.HTTPError as e:
        print(f"Publish failed: {e}")
        print(f"Response: {e.response.text if e.response else 'no response'}")
    except Exception as e:
        print(f"Publish failed: {e}")

    cur.close()
    conn.commit()  # explicit commit before close
    conn.close()


if __name__ == "__main__":
    main()