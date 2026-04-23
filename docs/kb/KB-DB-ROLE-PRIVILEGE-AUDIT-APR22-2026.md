# KB — Bluefin DB Role Privilege Audit (Apr 22 2026)

**Closes kanban duyuktv #1583** (redispatched-from-1514, DB Role Privilege Audit — Token Privilege Review).
**Status:** SHIPPED — 2 findings worth surfacing.

**Target:** zammad_production on bluefin (10.100.0.2), as-of Apr 22 2026 22:50 CT.

## Summary

17 active roles + postgres. Three superusers. One of them is unexpected.

## Roles + flags

| rolname | super | createdb | createrole | login | replication | bypassrls |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| **cherokee_helpdesk** | ✅ | | | ✅ | | |
| **claude** | ✅ | ✅ | ✅ | ✅ | ✅ | |
| **postgres** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| cherokee | | | | ✅ | | |
| cherokee_admin | | | | ✅ | | |
| cherokee_replication | | | | ✅ | ✅ | |
| cherokee_replicator | | | | ✅ | ✅ | |
| claude_user | | ✅ | | ✅ | | |
| council_jr | | | | ✅ | | |
| enhanced_memory_api | | | | ✅ | | |
| peace_chief_claude | | | | ✅ | | |
| svc_wopr_admin | | | | ✅ | | |
| tribal_codellama | | | | ✅ | | |
| tribal_llama32 | | | | ✅ | | |
| vetassist_admin | | | | ✅ | | |
| vetassist_api | | | | ✅ | | |
| war_chief_gpt4 | | | | ✅ | | |

## Finding 1 — cherokee_helpdesk has SUPERUSER

**Severity: HIGH** — Principle of least privilege violated.

The role named `cherokee_helpdesk` has the SUPERUSER flag. A role named "helpdesk" would typically need read-only or narrow-query privileges for ticket / support diagnosis. Granting SUPERUSER means anyone holding that credential can:
- Bypass all row-level security
- Modify any table
- DROP databases, users, extensions
- Read/write any data in any schema
- Alter system configuration

**Why this likely happened:** early-stage convenience during federation stand-up. Probably was meant to be "admin with helpdesk-adjacent responsibilities" and the flag was set broadly then never tightened.

**Recommendation:**
1. Audit `pg_stat_activity` history for which client IPs / applications currently use `cherokee_helpdesk` credentials. If unused, revoke SUPERUSER + DROP role.
2. If actively used, downgrade to specific grants: SELECT on relevant reporting tables + targeted INSERT/UPDATE on ticket tables only.
3. Rotate the credential after downgrade.

**Command to downgrade (after use-audit):**
```sql
ALTER ROLE cherokee_helpdesk NOSUPERUSER;
-- Then grant specific privileges:
-- GRANT SELECT ON <reporting_tables> TO cherokee_helpdesk;
```

## Finding 2 — claude role concentration

**Severity: MEDIUM** — Blast radius concentration.

The `claude` role has:
- SUPERUSER + CREATEDB + CREATEROLE + REPLICATION
- Membership in `council_jr`, `vetassist_admin`, `vetassist_api` — inherits all their privileges
- DELETE/INSERT/REFERENCES/SELECT/TRIGGER/TRUNCATE/UPDATE on 2,317 public tables

If the `claude` credential leaks, the attacker has full federation DB access plus the three inherited app-role privileges stacked on top. That's a massive blast radius.

**Why this likely happened:** TPM operational role needs broad access. Federation audits, LMC migrations, DLQ cleanup (today alone: 13 ticket status updates, 4 index migrations, role query) all happen as `claude`. The convenience is real.

**Recommendation:**
1. Keep `claude` as the operational TPM role — but restrict its *network* access. Only allow from known-host IPs (redfin, greenfin). Currently check `pg_hba.conf` for how broadly `claude` can connect.
2. Consider a pattern where TPM-level operations go through `claude` but Jr dispatch runs through a less-privileged role (maybe `council_jr` which is already set up with DELETE/INSERT/SELECT/UPDATE only on 752 tables — more appropriate scope).
3. For future migrations, consider a dedicated `tpm_migrator` role that gets CREATEDB + DDL privileges temporarily and is revoked after.

## Finding 3 — claude_user has CREATEDB

**Severity: LOW** — Minor excess.

`claude_user` has CREATEDB (can create new databases). No obvious reason for an application role to create databases on the fly. Could be legacy from initial federation setup.

**Recommendation:** audit whether `claude_user` is still used at all. If yes, remove CREATEDB. If no, drop the role.

## Role memberships

| Member | Member of |
|---|---|
| claude | council_jr |
| claude | vetassist_admin |
| claude | vetassist_api |

Only `claude` has inherited memberships. Clean otherwise. The inheritance is intentional — TPM can act as any of the specialist app roles — but compounds the blast-radius concern in Finding 2.

## Privilege distribution (public schema)

| Role | Tables with grants | Privileges |
|---|---:|---|
| claude | 2317 | DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE |
| council_jr | 752 | DELETE, INSERT, SELECT, UPDATE |

`council_jr` has a sensible app-role profile: CRUD without DDL. `claude` has effectively DDL too via SUPERUSER but the explicit grants show TRUNCATE and TRIGGER are wide. Worth reviewing whether TRUNCATE needs to be granted broadly.

## What this means for Owl Pass

Owl Pass (the federation-wide tech-debt + credential review sweep) should pick this up with:
- **cherokee_helpdesk superuser = top finding** for Owl to corroborate and track to closure
- **claude concentration = architectural concern** for Owl to propose a split-role recommendation
- **Apr 22 2026 data point** established; next Owl Pass can diff against this snapshot

## Next steps if Partner wants to act tonight

1. Confirm `cherokee_helpdesk` is unused OR plan the downgrade + credential rotation
2. Decide whether TPM operations split (claude vs tpm_migrator) is worth the engineering effort now
3. Archive this KB's snapshot; run the same query quarterly as a standing audit

## Cross-references

- Original failed attempt: kanban #1514 (Apr 17, JR failed "no executable steps")
- Redispatch: kanban #1583 (this KB's work)
- Companion: mac + linux credential sweeps (Apr 19 + Apr 22) — file-system-side surface. This KB is the DB-layer-side surface.
- For Owl Pass: this KB + the two credential sweeps together = complete audit input

## Apr 22 2026 TPM
