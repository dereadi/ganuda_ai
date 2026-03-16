# Jr Instruction: FARA Substack Sign-In via Chrome-MCP

**Epic**: Email Intelligence Pipeline
**Priority**: P2 (fast win — Deer content ingestion)
**Target Node**: sasass (192.168.132.241)
**Estimated SP**: 2

---

## Objective

Use FARA's browser control (chrome-mcp on sasass) to sign into Substack with Chief's email. This gives the cluster an authenticated Substack session to browse and ingest newsletter content from high-value sources (Nate Jones, etc.).

## Prerequisites

1. Chrome must be launched with `--remote-debugging-port=9222`
2. chrome-mcp must be running on sasass (Bun at `~/.bun/bin/bun`)
3. Gmail daemon must be running on redfin (to catch the verification code)

## Step 1: Ensure Chrome has remote debugging

On sasass, Chrome needs to be restarted with debugging enabled:

```bash
# Kill existing Chrome (save tabs first)
osascript -e 'tell application "Google Chrome" to quit'
sleep 2
# Relaunch with CDP
open -a "Google Chrome" --args --remote-debugging-port=9222
```

Verify: `curl -s http://localhost:9222/json/version` should return JSON.

## Step 2: Ensure chrome-mcp is running

```bash
cd /Users/Shared/ganuda/services/fara/chrome-mcp  # or wherever installed
~/.bun/bin/bun run start
```

If chrome-mcp is not installed yet, follow Phase 1 of:
`/ganuda/docs/jr_instructions/JR_BUILD_INSTRUCTIONS_FARA_BROWSER_CONTROL.md`

## Step 3: Navigate to Substack sign-in

Via chrome-mcp CDP commands:

1. Navigate to `https://substack.com/sign-in`
2. Wait for page load
3. Find the email input field
4. Type: `dereadi@gmail.com`
5. Click "Sign in" / "Continue" button
6. Substack will send a verification code to Gmail

## Step 4: Retrieve verification code from Gmail

Poll the `emails` table on bluefin for the incoming Substack code:

```sql
SELECT subject, body_text
FROM emails
WHERE from_address LIKE '%substack%'
  AND subject LIKE '%verification%'
ORDER BY received_at DESC
LIMIT 1;
```

Or use the Gmail API directly from the daemon to fetch the latest Substack email.

Extract the 6-digit code from the email body.

## Step 5: Enter verification code

Via chrome-mcp:

1. Find the verification code input field on the Substack page
2. Type the 6-digit code
3. Click "Verify" / "Continue"
4. Verify sign-in succeeded (look for profile icon or feed content)

## Step 6: Subscribe to high-value newsletters

Once signed in, navigate to and subscribe:

1. `https://natesnewsletter.substack.com` — Nate Jones (AI product strategy, 121K subscribers)
2. Any other newsletters Chief identifies

## Automation Notes

- The Gmail daemon polls every 120-300s. The verification code may take up to 5 minutes to appear in the DB.
- Substack verification codes expire after ~10 minutes. The automation must complete within that window.
- If chrome-mcp is not installed, this becomes a 2-part task: install chrome-mcp first, then sign in.

## Council Concerns

- **Crawdad**: This uses Chief's personal email. No credentials stored in code — OAuth token handles auth. Substack session cookie stays on sasass only.
- **Turtle**: If sign-in fails, no harm done. Fully reversible. Can sign out anytime.
- **Coyote**: Is automated Substack browsing actually better than the email daemon catching newsletters? YES — Substack's email delivery is inconsistent, and the web interface has content the emails don't include (comments, threads, recommendations).

## What NOT To Do

- Do NOT store the Substack password anywhere (there is no password — it's magic link / code auth)
- Do NOT automate payments or paid subscriptions without Chief approval
- Do NOT scrape content in bulk — browse like a human, read like a human
