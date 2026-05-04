#!/usr/bin/env python3
"""Initialize the federation ethos SQLite DB at /ganuda/data/ethos.db.

Council vote ratifying this build: 9625a058a103f582 (May 4 2026).
Federation-internal Phase 1; multi-tenant + audit-hash + valid_from/to +
sacred_pattern baked in for future external rollout (Phase 2).

Crawdad SECURITY mitigations applied: filesystem perms 600, WAL mode, SHA-256
audit hashes. Sacred-pattern guardrail enforced at write-API level (the service,
not this init script).

Idempotent — safe to re-run.
"""
import os
import sqlite3
import stat
import sys
from pathlib import Path

DB_PATH = Path(os.environ.get("ETHOS_DB_PATH", "/ganuda/data/ethos.db"))


SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS ethos_records (
  id                  INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id           TEXT NOT NULL DEFAULT 'cherokee_federation',
  term                TEXT NOT NULL,
  category            TEXT NOT NULL,
  definition          TEXT NOT NULL,
  context             TEXT,
  source              TEXT NOT NULL,
  council_audit_hash  TEXT NOT NULL,
  valid_from          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  valid_to            TIMESTAMP,
  sacred_pattern      BOOLEAN NOT NULL DEFAULT 0,
  created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CHECK (category IN (
    'indigenous_teaching',
    'council_voice',
    'patent',
    'dc_principle',
    'sacred_pattern',
    'governance',
    'architectural_commitment',
    'identity'
  ))
);

CREATE INDEX IF NOT EXISTS idx_ethos_term_active
  ON ethos_records (tenant_id, term)
  WHERE valid_to IS NULL;

CREATE INDEX IF NOT EXISTS idx_ethos_category_active
  ON ethos_records (tenant_id, category)
  WHERE valid_to IS NULL;

CREATE INDEX IF NOT EXISTS idx_ethos_sacred_active
  ON ethos_records (tenant_id)
  WHERE valid_to IS NULL AND sacred_pattern = 1;

CREATE TABLE IF NOT EXISTS ethos_audit_log (
  id                  INTEGER PRIMARY KEY AUTOINCREMENT,
  record_id           INTEGER,
  tenant_id           TEXT NOT NULL DEFAULT 'cherokee_federation',
  operation           TEXT NOT NULL,
  actor               TEXT NOT NULL,
  council_audit_hash  TEXT,
  timestamp           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  details             TEXT,
  CHECK (operation IN (
    'INSERT',
    'SUPERSEDE',
    'SACRED_UNFLAG',
    'SACRED_BLOCK',
    'TENANT_INIT'
  )),
  FOREIGN KEY (record_id) REFERENCES ethos_records(id)
);

CREATE INDEX IF NOT EXISTS idx_audit_tenant_time
  ON ethos_audit_log (tenant_id, timestamp);
"""


def init_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fresh = not path.exists()
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
    # Crawdad SECURITY mitigation: filesystem perms 600 (owner read/write only)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    print(f"  init_ethos_db: {path} ({'created' if fresh else 'verified'}), perms 600, WAL mode")


def verify(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode")
        jm = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM ethos_records")
        n_records = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM ethos_audit_log")
        n_audit = cur.fetchone()[0]
        cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_ethos%'")
        idxs = [r[0] for r in cur.fetchall()]
        st = path.stat()
        perms = oct(st.st_mode & 0o777)
        print(f"  verify: journal_mode={jm}, records={n_records}, audit={n_audit}, perms={perms}")
        print(f"          indexes={idxs}")
    finally:
        conn.close()


def main():
    print("=" * 60)
    print("ETHOS DB INIT — federation-internal Phase 1")
    print(f"DB path: {DB_PATH}")
    print(f"Council ratification: 9625a058a103f582 (May 4 2026)")
    print("=" * 60)
    init_db(DB_PATH)
    verify(DB_PATH)
    print("\nReady.")


if __name__ == "__main__":
    main()
