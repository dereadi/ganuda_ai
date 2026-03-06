# KB-WEB-CONTENT-MATERIALIZER-PIPELINE-FEB27-2026

**Status**: LIVE
**Deployed**: 2026-02-27
**Last Updated**: 2026-03-02
**Domain**: Infrastructure / Web Publishing
**Related Council Vote**: #b875a756efe895d0 (Option B: Postgres + File Cache, APPROVED)

---

## Summary

The web content system provides a database-backed publishing pipeline for ganuda.us. Content is authored on redfin, pushed to a PostgreSQL table on bluefin, and materialized to static files on both DMZ web nodes (owlfin + eaglefin) within 30 seconds. The architecture separates write authority (cluster LAN) from serving infrastructure (DMZ), with graceful degradation if the database becomes unreachable.

---

## Architecture

### Database: web_content Table

- **Host**: bluefin — 192.168.132.222:5432
- **Database**: zammad_production
- **User**: claude
- **Table**: web_content

**Schema:**

| Column | Type | Notes |
|---|---|---|
| id | serial | Primary key |
| site | varchar | e.g. `ganuda.us` |
| path | varchar | URL path, e.g. `/blog/post.html` |
| content_type | varchar | MIME type, e.g. `text/html` |
| content | text | Full file content |
| content_hash | varchar(64) | SHA-256 hex digest of content |
| metadata | jsonb | Arbitrary metadata (title, tags, etc.) |
| published | boolean | True = live, False = pulled from serving |
| created_at | timestamptz | Auto-set on insert |
| updated_at | timestamptz | Auto-updated by trigger |
| created_by | varchar | Who or what inserted the record |

**Indexes:**
- Unique index on `(site, path)` — enforces one record per URL

**Trigger:**
- `trg_web_content_updated` — fires BEFORE UPDATE, sets `updated_at = NOW()` automatically

---

## Materializer Daemon

**Script**: `/ganuda/services/web_materializer.py`

**Deployed on:**
- owlfin — 192.168.132.170 (DMZ primary, keepalived MASTER)
- eaglefin — 192.168.132.84 (DMZ failover, keepalived BACKUP)

**Service name**: `web-materializer.service` (systemd, on both nodes)

**Web root**: `/home/dereadi/www/ganuda.us/` on each DMZ node

**Caddy**: Serves static files directly from web root. No application layer in the hot path.

### Polling Logic

1. Every 30 seconds, queries `web_content WHERE site = 'ganuda.us'`
2. For each row where `published = true`:
   - Computes SHA-256 of local file at web root path (if file exists)
   - Compares against `content_hash` in DB
   - Only writes file to disk if hashes differ (avoids unnecessary I/O)
3. For rows where `published = false` or deleted from DB:
   - Removes corresponding local file if present
4. Creates parent directories as needed before writing

### Graceful Degradation

If the database is unreachable (bluefin down, network partition, etc.):
- Materializer logs the error and sleeps
- Previously written static files remain on disk
- Caddy continues serving stale cache — site stays up
- No attempt to delete or modify existing files during DB outage

---

## Publishing Workflow

### Standard Publish

1. Edit source files on redfin at `/ganuda/www/ganuda.us/`
2. Run the publish script:

```text
python3 /ganuda/scripts/publish_web_content.py <file>
```

The script:
- Reads the file
- Computes SHA-256
- Upserts into `web_content` (INSERT ... ON CONFLICT (site, path) DO UPDATE)
- Sets `published = true`, `updated_at = NOW()`

3. Within 30 seconds, materializer picks up the change on both owlfin and eaglefin
4. Caddy begins serving the new content immediately after file write

### Unpublish

```text
python3 /ganuda/scripts/publish_web_content.py <file> --unpublish
```

Sets `published = false`. Materializer removes the file from web root on next poll cycle.

### Seeding

Initial content was seeded using:

```text
python3 /ganuda/scripts/seed_web_content.py
```

This script bulk-inserts all files from the source directory into `web_content`.

---

## Current Content (as of 2026-03-02)

- **15 published pages** on ganuda.us
- **10 blog posts** + 1 blog index page
- **Site design**: Dark theme — navy, charcoal, gold, teal. Cherokee syllabary displayed in footer.

---

## Known Gap: Blog Index Auto-Regeneration

**Identified**: 2026-03-02

**Problem**: The blog index page (`/blog/index.html`) is manually maintained. When a new blog post is published via `publish_web_content.py`, the index is NOT automatically updated to include it.

**Root cause**: The publish script has no awareness of index pages or site structure. It treats every file as an independent document.

**Symptoms**: New blog post appears at its direct URL but is invisible from the blog index navigation.

**Fix queued**: Jr task `BLOG-INDEX-AUTOREGEN` — creates `regenerate_blog_index.py` script that:
- Queries `web_content` for all published blog posts
- Regenerates `/blog/index.html` with correct links
- Can be run standalone or wired into the publish script as a post-hook

**Immediate workaround applied (2026-03-02)**: Manual DB update to insert/update the Natural Falls blog post entry directly.

---

## DMZ Architecture

```
                    Internet
                        |
              keepalived VIP: 192.168.30.10
                   /            \
          owlfin:30.2        eaglefin:30.3
          (MASTER)            (BACKUP)
        Caddy static          Caddy static
          web root              web root
             |                     |
      web-materializer      web-materializer
          (polls)               (polls)
             \                   /
              bluefin:5432
              web_content table
```

Both DMZ nodes independently poll the same DB table and maintain identical static file sets. Keepalived VIP floats between them. If owlfin fails, eaglefin takes the VIP and is already current with all content.

---

## Related Files

| Path | Purpose |
|---|---|
| `/ganuda/services/web_materializer.py` | Materializer daemon |
| `/ganuda/scripts/publish_web_content.py` | Publish / unpublish single file |
| `/ganuda/scripts/seed_web_content.py` | Bulk seed from directory |
| `/ganuda/www/ganuda.us/` | Source files on redfin (authoring side) |
| `/home/dereadi/www/ganuda.us/` | Web root on owlfin + eaglefin (serving side) |

---

## Operational Notes

- **Do not edit files directly on owlfin or eaglefin web root** — materializer will overwrite on next poll
- **Content hash drift**: If local file is edited on DMZ node manually, next materializer poll will overwrite with DB content
- **Logs**: Check `journalctl -u web-materializer.service` on owlfin or eaglefin for poll status and write events
- **DB credentials**: Stored in `/opt/ganuda/secrets.env` on DMZ nodes — NOT in the repository
- **Port**: Materializer uses standard psycopg2 connection to bluefin:5432 — no WireGuard required (same LAN segment via .132)

---

## Council Vote Reference

**Vote ID**: #b875a756efe895d0
**Decision**: Option B approved — Postgres-backed table as source of truth with file cache on DMZ nodes
**Rationale**: Simple, auditable, no additional services. Postgres already deployed on bluefin. File cache means web serving has zero DB dependency in steady state.

---

*Recorded by TPM. Long Man RECORD step for Web Content Materializer Pipeline.*
