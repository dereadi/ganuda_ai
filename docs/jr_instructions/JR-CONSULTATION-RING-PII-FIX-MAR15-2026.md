# Jr Instruction: Fix PII Tokenization in Consultation Ring

**Task**: Install presidio-analyzer in ganuda venv OR wire domain_tokenizer to call greenfin PII service
**Priority**: P1 (PII leaking through air-gap proxy)
**Story Points**: 2
**Date**: 2026-03-15

## Problem

The consultation ring's domain tokenizer (`/ganuda/lib/domain_tokenizer.py`) composes PIIService (Presidio-based) for PII detection. But `presidio-analyzer` is NOT installed in `/ganuda/venv/`. The tokenizer silently falls back to infra-only tokenization (line 147-150), and PII (SSN, names, phone numbers) passes through to frontier models unmasked.

**Verified**: Sent "Patient John Smith SSN 123-45-6789" through `/consult` endpoint — `pii_replaced: 0`, name and SSN went to the model in plaintext.

## Options (pick one)

### Option A: Install Presidio locally on redfin (simpler, ~500MB)
```bash
/ganuda/venv/bin/pip install presidio-analyzer presidio-anonymizer spacy
/ganuda/venv/bin/python -m spacy download en_core_web_lg
```

Then restart: `sudo systemctl restart consultation-ring.service`

### Option B: Call greenfin PII service via HTTP (lighter, network-dependent)
Greenfin runs PII as a service at `192.168.132.224:8003` (or check actual port). Modify `_get_pii_service()` in domain_tokenizer.py to call the remote service instead of importing Presidio locally.

**Recommend Option A** — the air-gap proxy must work even if greenfin is down. PII tokenization on the same node as the consultation ring is more reliable and lower latency.

## After Fix

Re-test:
```bash
curl -s -X POST http://localhost:9400/consult \
  -H "Content-Type: application/json" \
  -d '{"query": "Patient John Smith SSN 123-45-6789 needs help", "domain": "general"}'
```

Expected: `pii_replaced: 2` (name + SSN), neither "John Smith" nor "123-45-6789" appears in the model's response context.

## Acceptance Criteria

1. PII (SSN, names, phone numbers, emails) is tokenized before crossing the boundary
2. `pii_replaced` count is non-zero when PII is present in input
3. Infra tokenization continues to work (node names, IPs)
4. Service restarts cleanly after dependency install

## Do NOT

- Remove the silent fallback (line 147-150) — it's a safety net, keep it
- Add logging that includes the PII itself (log the token count, not the values)
- Change the token format — must stay `<TOKEN:hexdigest>` for consistency
