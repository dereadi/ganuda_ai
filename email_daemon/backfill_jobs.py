#!/usr/bin/env python3
"""Backfill job classification for existing emails."""
import psycopg2
from job_classifier import is_job_related, classify_job_email, extract_company_position

conn = psycopg2.connect(host='192.168.132.222', database='triad_federation', user='claude', password='jawaseatlasers2')
cur = conn.cursor()
cur.execute("SELECT id, from_address, subject, body_text FROM emails WHERE job_classification IS NULL")
rows = cur.fetchall()
updated = 0
for row in rows:
    email_id, from_addr, subject, body = row
    if is_job_related(from_addr or '', subject or ''):
        classification, priority = classify_job_email(from_addr or '', subject or '', body or '')
        company, position = extract_company_position(from_addr or '', subject or '', body or '')
        if classification:
            cur.execute("UPDATE emails SET job_classification = %s, job_company = %s, job_position = %s WHERE id = %s",
                       (classification, company, position, email_id))
            updated += 1
            print(f"{classification}: {(subject or '')[:60]}")
conn.commit()
print(f"\nTotal classified: {updated}")
cur.close()
conn.close()
