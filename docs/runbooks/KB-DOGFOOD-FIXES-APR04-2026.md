# KB: Dogfood Fixes — Apr 4, 2026

## Context
First real dogfooding session across all four products. Found bugs in 5 minutes.

## Fix 1: Canary — stderr/stdout mixing breaks JSON pipe

**Problem:** `canary.py --json` output included status messages ("Scanning ports...") on stdout, corrupting JSON pipe.

**Fix:** Changed all `print("Scanning...")` to `print("Scanning...", file=sys.stderr)` in `run_full_scan()`.

**File:** `/ganuda/products/security-canary/canary.py`

**Test:** `python3 canary.py --quick --json 2>/dev/null | python3 -m json.tool` should parse cleanly.

## Fix 2: Trimmer — non-subscription domains leaking through

**Problem:** Uber (7x), Grubhub, Costco, Hilton, Steam, Kraken, MLOps Community, Credit Karma all showing as subscription signals. These are one-time purchases, food delivery, or marketing — not recurring subscriptions.

**Fix:** Added 10 domains to `NON_SUBSCRIPTION_DOMAINS` in `scanner.py`:
- uber.com, eat.grubhub.com, orders.grubhub.com (food/transport)
- creditkarma.com, news.mlops.community (marketing)
- no-reply@hilton.com, digital.costco.com, steampowered.com (one-time)
- kraken.com, email.kraken.com (crypto marketing)

**Result:** 44 raw → 31 filtered (was 42). Uber and Grubhub confirmed removed.

**File:** `/ganuda/products/subscription-trimmer/scanner.py`

## Fix 3 (Noted, not fixed): Canary remote node scanning

**Problem:** Can't scp canary to bluefin/owlfin and run cleanly — missing config_checker.py in the copy, and the ss/lsof commands have different output formats on different nodes.

**Fix needed:** Package canary as a single-file scanner or create an install script that copies all required files. Add to the Podman test pipeline when it's ready.

## Fix 4 (Noted, not fixed): Meeting Notes needs real audio

**Problem:** No real meeting data. Demo uses a synthetic transcript.

**Fix needed:** Record the Khalid call (with consent) or any real meeting. Process with the extractor. Replace demo with real data.

## Lesson

Five minutes of dogfooding found four bugs that weeks of development didn't. Products aren't done when they deploy. They're done when the builder eats them daily.

---

*For Seven Generations.*
