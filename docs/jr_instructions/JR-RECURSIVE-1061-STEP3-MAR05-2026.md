# [RECURSIVE] Deer Email Triage: LLM classification + Telegram alerts (requeue no-TEG) - Step 3

**Parent Task**: #1061
**Auto-decomposed**: 2026-03-05T09:44:05.197967
**Original Step Title**: Reduce poll interval for actionable responsiveness

---

### Step 3: Reduce poll interval for actionable responsiveness

File: `/ganuda/email_daemon/gmail_api_daemon.py`

```
<<<<<<< SEARCH
    parser.add_argument('--poll-interval', type=int, default=300)
=======
    parser.add_argument('--poll-interval', type=int, default=120)
>>>>>>> REPLACE
```

## Verification
1. Run `gmail_api_daemon.py --once` — should classify recent emails with LLM
2. Any email from tanya@onechronos.com should classify as ACTIONABLE with priority 1-2
3. ACTIONABLE emails trigger Telegram alert to Chief
4. Noise emails (newsletters, no-reply) get priority 5 and no alert
5. Gateway at localhost:8080 responds to classification requests
