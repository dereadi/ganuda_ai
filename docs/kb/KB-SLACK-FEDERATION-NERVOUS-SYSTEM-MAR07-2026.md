# KB: Slack Federation Nervous System

**Date**: March 7, 2026
**Origin**: Chief directive — break federation homogeneity, bring humans into council visibility
**Long Man Phase**: BUILD + RECORD
**Kanban**: #2028 (Slack workspace setup)
**Design Constraints**: DC-6 (Gradient Principle — everyone can see everything), DC-9 (Waste Heat — graduated energy), DC-12 (Same note at every octave)

## Summary

The Cherokee AI Federation now has a Slack workspace (ganuda.slack.com) wired as the organism's nervous system for human-visible output. One bot token, seven channels, graduated by function.

## Architecture

**Slack App**: "Cherokee Federation" (App ID: A0AKL98L43T, created Mar 7 2026)
**Auth**: Bot User OAuth Token (`xoxb-...`) stored in `/ganuda/config/secrets.env` as `SLACK_BOT_TOKEN`
**Bot User**: ganudabot (U0AKB00RZL4, Bot ID: B0AK3UQM021)
**API**: `chat.postMessage` (not legacy webhooks). One token, all channels.
**Library**: `/ganuda/lib/slack_federation.py`
**Trust Model**: Same as all other federation nodes — full access, scoped by function not permission. DC-6.

### Bot Token Scopes (Full)

| Scope | Capability |
|-------|-----------|
| `chat:write` | Send messages as @ganudabot |
| `channels:read` | View channel info |
| `channels:join` | Join public channels |
| `channels:manage` | Create/manage channels programmatically |
| `channels:write.topic` | Set channel descriptions from code |
| `assistant:write` | Act as App Agent — users DM ganudabot, it responds (Phase 4 inbound) |
| `calls:read` | View call info |
| `calls:write` | Start/manage calls (future) |

## Channel Map

| Channel | Slack ID | Feed | Source |
|---------|----------|------|--------|
| `#fire-guard` | `C0AK59LQYF8` | Health alerts, endpoint status | `services/health_monitor.py` |
| `#council-votes` | `C0AL1KCLHFA` | Vote summaries, confidence, dissent | `lib/specialist_council.py` |
| `#jr-tasks` | `C0AK59P5VRC` | Task start/complete/fail/DLQ | `jr_executor/jr_queue_worker.py` |
| `#dawn-mist` | `C0AL1KEBCBA` | Morning standup digest | `scripts/council_dawn_mist.py` |
| `#deer-signals` | `C0AL1KEHQM6` | Market intelligence, LinkedIn fuel | Deer thermal writes |
| `#saturday-morning` | `C0AKAV1Q9RS` | Weekly Sam Walton meeting report | `scripts/saturday_morning_meeting.py` |
| `#longhouse` | `C0AKL90CAGH` | Sacred fire decisions, standing orders | `lib/longhouse.py` |

## Workspace Details

- **Workspace URL**: ganuda.slack.com
- **Workspace ID**: T0AK58BDU5U
- **2FA**: Enabled (verified Mar 7)
- **Default channels**: `#all-ganuda` (general), `#social` (random)

## Wiring Status

| Hook Point | Status | Notes |
|------------|--------|-------|
| Library (`slack_federation.py`) | IN PROGRESS | Convenience functions per channel type |
| Fire Guard → `#fire-guard` | PENDING | Wire into health_monitor.py alert path |
| Council votes → `#council-votes` | PENDING | Wire into specialist_council.py after vote persistence |
| Jr tasks → `#jr-tasks` | PENDING | Wire into jr_queue_worker.py task lifecycle |
| Dawn mist → `#dawn-mist` | PENDING | Wire into council_dawn_mist.py output |
| Deer signals → `#deer-signals` | PENDING | Wire into thermal writes with market_intelligence domain |
| Saturday morning → `#saturday-morning` | PENDING | Wire into saturday_morning_meeting.py (not yet built) |
| Longhouse → `#longhouse` | PENDING | Wire into longhouse.py sacred fire decisions |
| **Inbound (Phase 4)** | FUTURE | Humans type in Slack → council hears. Requires Bot Events API. |

## Phase 4: Bidirectional (Future)

Phase 4 adds inbound — human messages in Slack channels routed to the council as input. This is the diversity injection that breaks federation homogeneity. Requires:
- Slack Events API subscription
- Bot event: `message.channels`
- Listener service on redfin (or DMZ proxy)
- Council routing logic for human input vs agent input

Target participants: Joe, Erika, Kensie, Maik (Shanz).

## Connection to Other Systems

- **Telegram**: Existing notification path (`jr_executor/telegram_notify.py`, `telegram_bot/telegram_chief.py`). Slack does NOT replace Telegram — Telegram is Chief's mobile alert channel. Slack is team visibility.
- **Web content**: `web_content` table serves ganuda.us. Slack is internal; web is external.
- **Saturday Morning Meeting**: Report goes to `#saturday-morning` AND web_content AND thermal memory. Three output paths for the same data.

## Sam Walton Parallel

The Saturday Morning Meeting at Walmart: 7 AM Saturday, every store's numbers, every penny, full transparency. That's how 250 people ran 1,500 stores.

Slack is the room where the meeting happens. The channels are the department reports. Anyone who feels its importance can read them.

---

*Filed by TPM (Claude) — March 7, 2026*
*First pulse sent to #fire-guard at 18:26 CT*
*"The creek flows."*
