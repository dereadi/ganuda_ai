# Jr Build Instruction: Subscription Trimmer — "What Am I Paying For?"

## Priority: P1 — MOCHA Product Sprint
## Date: April 2, 2026
## Requested By: Partner + TPM
## Target: Product Hunt-ready MVP in 2-3 days

---

## What We're Building

A tool that scans your email for recurring subscription charges, identifies every service you're paying for, shows you what you forgot about, and tells you how much you'd save by canceling the ones you don't use.

**Not a chatbot. Not a dashboard with fake data. A real scanner that reads real emails and finds real money.**

## Why This Is Low-Hanging Fruit

We already have:
- **Gmail API integration** — authenticated, token at `~/.gmail_credentials/token.pickle`, daemon at `/ganuda/email_daemon/gmail_api_daemon.py`
- **LLM inference** — vLLM running Qwen2.5-72B for classification
- **Structured output** — council architecture already produces structured JSON from unstructured text
- **Web deployment** — Caddy on DMZ, FastAPI on owlfin, ganuda.us live

## Architecture

```
Gmail API → Fetch receipts/invoices → LLM classifies → Structured output → Web dashboard

1. SCAN: Pull emails matching subscription patterns (receipts, invoices, "your payment", "renewal", "subscription")
2. CLASSIFY: LLM extracts: service name, amount, frequency (monthly/annual), last charge date
3. DEDUPE: Group by service, merge multiple emails for same subscription
4. SCORE: Flag stale subscriptions (charged but never mentioned in non-billing emails = probably forgotten)
5. DISPLAY: Clean web page showing all subscriptions, total monthly burn, savings opportunities
```

## Phase 1: Scanner Backend (Day 1)

### Task 1A: Gmail Subscription Scanner

Build `/ganuda/products/subscription-trimmer/scanner.py`:

```python
# Core logic:
# 1. Connect to Gmail via OAuth token
# 2. Search for subscription-related emails (last 90 days)
#    Queries: "receipt", "invoice", "your payment", "subscription renewed",
#             "billing statement", "you've been charged", "auto-renewal"
# 3. For each email, extract:
#    - From address (identifies the service)
#    - Subject line
#    - Date
#    - Body snippet (first 500 chars)
# 4. Return list of raw subscription signals
```

Search queries to use:
```
"your payment" OR "subscription" OR "invoice" OR "receipt" OR "renewal" OR "billing" OR "you've been charged" OR "auto-pay"
```

Filter out:
- Upwork payment receipts (that's income, not subscription)
- One-time purchases (no recurring pattern)
- Spam/promotional (look for actual charge confirmations)

### Task 1B: LLM Classifier

Build `/ganuda/products/subscription-trimmer/classifier.py`:

For each email signal, send to LLM with structured output prompt:

```
Analyze this email and extract subscription information.
Return JSON:
{
  "is_subscription": true/false,
  "service_name": "Netflix",
  "amount": 15.99,
  "currency": "USD",
  "frequency": "monthly",  // monthly, annual, quarterly, weekly
  "charge_date": "2026-03-15",
  "category": "entertainment",  // entertainment, productivity, cloud, fitness, news, shopping, finance, other
  "confidence": 0.95
}
If this is not a subscription charge, set is_subscription to false.
```

Use local vLLM (http://localhost:8000) — NOT external API. Sovereign.

### Task 1C: Aggregator

Build `/ganuda/products/subscription-trimmer/aggregator.py`:

- Group classified results by service_name
- Calculate: monthly total, annual total, per-service monthly cost
- Identify "ghost subscriptions" — services that charged you but you haven't opened emails from (non-billing) in 30+ days
- Sort by: most expensive first, then ghost subscriptions

Output structure:
```json
{
  "scan_date": "2026-04-02",
  "email": "dereadi@gmail.com",
  "total_monthly": 247.83,
  "total_annual": 2973.96,
  "subscription_count": 14,
  "ghost_count": 3,
  "potential_savings": 45.97,
  "subscriptions": [
    {
      "service": "Netflix",
      "amount": 15.99,
      "frequency": "monthly",
      "category": "entertainment",
      "last_charge": "2026-03-15",
      "is_ghost": false,
      "last_non_billing_email": "2026-03-20"
    }
  ]
}
```

## Phase 2: Web Dashboard (Day 2)

### Task 2A: FastAPI Backend

Build `/ganuda/products/subscription-trimmer/api.py`:

- `GET /` — landing page (HTML)
- `POST /scan` — trigger scan (returns job ID)
- `GET /results/{job_id}` — get scan results
- `GET /demo` — show demo results from Partner's email (pre-scanned, cached)

### Task 2B: Simple HTML Dashboard

Single page, no framework. Clean design matching ganuda.us style:

- Header: "What Am I Paying For?" + total monthly burn (big number)
- Cards for each subscription: service name, amount, frequency, category icon
- Ghost subscriptions highlighted in amber: "You haven't used this in 30+ days"
- Bottom: "You could save $X/month by canceling ghost subscriptions"
- Link to ganuda.us: "Built by Cherokee AI Federation — sovereign, no cloud"

### Task 2C: Deploy to DMZ

Deploy on owlfin alongside stoneclad_demo_api:
- Port 8501
- Caddy route: ganuda.us/trimmer/*
- Use the cross-node deployment KB

## Phase 3: Polish for Product Hunt (Day 3)

- README with screenshots
- Privacy statement: "Your email is scanned locally. No data leaves your network. No third-party APIs. Sovereign."
- Open source the scanner on GitHub (dereadi/subscription-trimmer)
- Product Hunt listing draft
- Demo video (30 seconds — scan, see results, see savings)

## Technical Constraints

- **Gmail only for MVP** — Outlook/Yahoo later
- **OAuth required** — user must authenticate their own Gmail
- **Local LLM only** — no OpenAI/Anthropic API calls. All inference on redfin vLLM.
- **No stored credentials** — token in user's local filesystem only
- **PII handling** — email content never logged to thermal memory. Scan results only (service names + amounts, no email bodies).

## Why This Wins on Product Hunt

1. **Privacy story** — "Unlike Mint/Truebill, we never see your data. Everything runs locally."
2. **AI-powered but not AI-hyped** — the LLM does real work (classification), not chatbot fluff
3. **Real money saved** — people love seeing "you're wasting $47/month on stuff you forgot about"
4. **Open source** — builds trust, drives GitHub stars, fills the profile gap
5. **Nate Jones validated** — his Mythos video literally said "tell your AI to find $200 in savings from subscriptions"

## Success Criteria

- [ ] Scanner pulls real subscription emails from Gmail
- [ ] LLM correctly classifies 90%+ of subscriptions
- [ ] Aggregator identifies ghost subscriptions
- [ ] Dashboard shows total burn, per-service cards, savings estimate
- [ ] Deployed on ganuda.us/trimmer
- [ ] Open sourced on GitHub
- [ ] Demo video recorded
- [ ] Product Hunt listing drafted

---

*Nate Jones, Mythos video, Apr 1 2026: "Just tell your AI — look at my recurring subscriptions and find me $200 in savings. Most households can find $200 a month somewhere."*

*We're building the tool that does exactly that. Sovereign. Local. Real.*

*For Seven Generations.*
