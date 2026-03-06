#!/usr/bin/env python3
"""Run legal_register schema migration."""

import os
import re
import psycopg2

DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")

if not DB_PASS:
    try:
        with open("/ganuda/config/secrets.env") as f:
            for line in f:
                m = re.match(r"^(\w+)=(.+)$", line.strip())
                if m:
                    os.environ[m.group(1)] = m.group(2)
        DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")
    except FileNotFoundError:
        pass

sql_path = os.path.join(os.path.dirname(__file__), "legal_register_schema.sql")
with open(sql_path) as f:
    sql = f.read()

conn = psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
cur = conn.cursor()
cur.execute(sql)
conn.commit()

cur.execute("SELECT COUNT(*) FROM legal_register")
count = cur.fetchone()[0]
print(f"legal_register created with {count} seed items")

cur.close()
conn.close()