#!/usr/bin/env python3
"""Clipboard search and CLI interface."""

import sqlite3
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = os.path.expanduser("~/.clipboard_intel/clips.db")


def get_conn():
    if not os.path.exists(DB_PATH):
        print(f"No database found at {DB_PATH}. Run the monitor first.")
        sys.exit(1)
    return sqlite3.connect(DB_PATH)


def search(query: str = None, clip_type: str = None, today: bool = False,
           hot: bool = False, limit: int = 20) -> List[Dict]:
    conn = get_conn()
    conn.row_factory = sqlite3.Row

    sql = "SELECT * FROM clips WHERE 1=1"
    params = []

    if query:
        sql += " AND (content LIKE ? OR content_preview LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])
    if clip_type:
        sql += " AND clip_type = ?"
        params.append(clip_type)
    if today:
        sql += " AND timestamp > datetime('now', '-1 day')"

    if hot:
        sql += " ORDER BY temperature DESC"
    else:
        sql += " ORDER BY timestamp DESC"

    sql += " LIMIT ?"
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats() -> Dict:
    conn = get_conn()
    cur = conn.execute("SELECT COUNT(*), AVG(temperature), MAX(temperature) FROM clips")
    total, avg_t, max_t = cur.fetchone()
    cur = conn.execute("SELECT clip_type, COUNT(*) FROM clips GROUP BY clip_type ORDER BY COUNT(*) DESC")
    by_type = dict(cur.fetchall())
    cur = conn.execute("SELECT COUNT(*) FROM clips WHERE is_sensitive = 1")
    sensitive = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM clips WHERE timestamp > datetime('now', '-1 day')")
    today = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM clips WHERE is_pinned = 1")
    pinned = cur.fetchone()[0]
    conn.close()
    return {
        "total": total or 0, "avg_temperature": round(avg_t or 0, 1),
        "max_temperature": max_t or 0, "by_type": by_type,
        "sensitive": sensitive, "today": today, "pinned": pinned,
    }


def pin_clip(clip_id: int):
    conn = get_conn()
    conn.execute("UPDATE clips SET is_pinned = 1, temperature = 95 WHERE id = ?", (clip_id,))
    conn.commit()
    conn.close()
    print(f"Pinned clip #{clip_id} (temperature → 95)")


def delete_clip(clip_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM clips WHERE id = ?", (clip_id,))
    conn.commit()
    conn.close()
    print(f"Deleted clip #{clip_id}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Clipboard Intelligence — Search & Manage")
    sub = parser.add_subparsers(dest="command")

    s = sub.add_parser("search", help="Search clips")
    s.add_argument("query", nargs="?", default=None)
    s.add_argument("--type", dest="clip_type")
    s.add_argument("--today", action="store_true")
    s.add_argument("--hot", action="store_true")
    s.add_argument("--limit", type=int, default=20)

    sub.add_parser("stats", help="Show statistics")

    p = sub.add_parser("pin", help="Pin a clip")
    p.add_argument("id", type=int)

    d = sub.add_parser("delete", help="Delete a clip")
    d.add_argument("id", type=int)

    sub.add_parser("list", help="List recent clips")

    args = parser.parse_args()

    if args.command == "search":
        results = search(args.query, args.clip_type, args.today, args.hot, args.limit)
        for r in results:
            temp_bar = "█" * int(r["temperature"] / 10) + "░" * (10 - int(r["temperature"] / 10))
            sens = " 🔒" if r["is_sensitive"] else ""
            pin = " 📌" if r["is_pinned"] else ""
            print(f"  #{r['id']:>4} | {r['clip_type']:12} | {temp_bar} {r['temperature']:>5.1f}° | {r['content_preview'][:50]}{sens}{pin}")

    elif args.command == "stats":
        s = get_stats()
        print(f"Total clips: {s['total']}")
        print(f"Avg temperature: {s['avg_temperature']}°")
        print(f"Today: {s['today']} | Sensitive: {s['sensitive']} | Pinned: {s['pinned']}")
        print("By type:")
        for t, c in s["by_type"].items():
            print(f"  {t:15} {c}")

    elif args.command == "pin":
        pin_clip(args.id)

    elif args.command == "delete":
        delete_clip(args.id)

    elif args.command == "list" or args.command is None:
        results = search(limit=15)
        for r in results:
            temp_bar = "█" * int(r["temperature"] / 10) + "░" * (10 - int(r["temperature"] / 10))
            print(f"  #{r['id']:>4} | {r['clip_type']:12} | {temp_bar} | {r['content_preview'][:50]}")


if __name__ == '__main__':
    main()
