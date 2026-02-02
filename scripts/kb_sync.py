#!/usr/bin/env python3
"""
KB Sync - Synchronize markdown KB files to kb_article_log table.
Cherokee AI Federation - For Seven Generations
"""

import os
import hashlib
import re
from datetime import datetime
import psycopg2
from pathlib import Path

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

KB_DIRS = [
    '/ganuda/docs/kb',
    '/Users/Shared/ganuda/docs/kb'  # macOS path
]


def extract_metadata(content: str) -> dict:
    """Extract metadata from KB markdown file."""
    metadata = {
        'title': '',
        'category': 'General',
        'kb_id': None
    }

    # Extract title from first # heading
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if title_match:
        metadata['title'] = title_match.group(1).strip()

    # Extract KB ID
    kb_id_match = re.search(r'\*\*KB ID\*\*:\s*(KB-[\w-]+)', content)
    if kb_id_match:
        metadata['kb_id'] = kb_id_match.group(1)

    # Extract category
    cat_match = re.search(r'\*\*Category\*\*:\s*(.+)$', content, re.MULTILINE)
    if cat_match:
        metadata['category'] = cat_match.group(1).strip()

    return metadata


def hash_content(content: str) -> str:
    """Generate content hash for change detection."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def sync_kb_file(cursor, file_path: str):
    """Sync a single KB file to database."""
    with open(file_path, 'r') as f:
        content = f.read()

    metadata = extract_metadata(content)
    content_hash = hash_content(content)

    # Check if article exists
    cursor.execute(
        "SELECT article_id, article_hash FROM kb_article_log WHERE file_path = %s",
        (file_path,)
    )
    existing = cursor.fetchone()

    if existing:
        # Update if content changed
        if existing[1] != content_hash:
            cursor.execute("""
                UPDATE kb_article_log
                SET article_hash = %s, title = %s, content = %s,
                    category = %s, last_modified = NOW()
                WHERE file_path = %s
            """, (content_hash, metadata['title'], content,
                  metadata['category'], file_path))
            return 'updated'
        return 'unchanged'
    else:
        # Insert new article
        cursor.execute("""
            INSERT INTO kb_article_log
            (article_hash, title, content, category, author, created_at,
             last_modified, access_count, validation_status, file_path)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW(), 0, 'pending', %s)
        """, (content_hash, metadata['title'], content,
              metadata['category'], 'kb_sync', file_path))
        return 'created'


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    stats = {'created': 0, 'updated': 0, 'unchanged': 0}

    for kb_dir in KB_DIRS:
        if not os.path.exists(kb_dir):
            continue

        for file_path in Path(kb_dir).glob('*.md'):
            result = sync_kb_file(cursor, str(file_path))
            stats[result] += 1
            print(f"  {result}: {file_path.name}")

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\nSync complete: {stats}")


if __name__ == '__main__':
    main()