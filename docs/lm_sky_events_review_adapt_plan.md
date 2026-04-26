# LM-SKY-EVENTS-REVIEW — Adapt Phase Plan

**Author:** TPM (Stoneclad)
**Date:** Apr 25 2026
**Trigger:** Apr 25 storm-window incident — Partner driving into storm couldn't glance at home cameras from phone via ganudabot. Diagnostic also surfaced /ganuda at 100% from unbounded sky_events accumulation (717G in 33d, ~21G/day).

## Scope

Two parallel tracks:

**Track A (standalone, immediate):** Add `/glance <camera>` Telegram command to ganudabot so Partner can pull a live frame from his phone. Solves the storm-window pain.

**Track B (epic, multi-Jr):** Wire SAG Cameras view to historical sky_events, add 14d retention, lightning-flag preserve, Slack alert feed. Turns 2,235 accumulated events from cost-center into reviewable signal.

## Partner prerequisites
**None** — both tracks are local infra + code. TPM + Jr executable.

## Track A: ganudabot /glance — Single Jr atomic

| # | Unit | Owner | File | Size |
|---|---|---|---|---|
| A1 | `/glance <camera>` Telegram command | Jr | `/ganuda/telegram_bot/derpatobot_claude.py` | 30 min |

Independent of Track B. No DAG.

## Track B: Sky events review — DAG

```
B1 (lightning flag — defines what to preserve)
  ↓
B2 (backend wire-up — /api/cameras/events endpoint, glob sky_events/)
  ↓                                                         ↓
B3 (frontend wire-up — MotionEventTimeline reads /events)   B4 (slack alert watcher — inotify on sky_events/)
                                                            ↓
                                                            B5 (retention purger — daily cron, 14d, exempt flagged)
```

B5 must wait until B1 lands so flagged events aren't deleted before being marked.
B4 can land any time after B1 (alerts work without timeline; nice to have ⚡ flag in caption).
B3 can land any time after B2.

## Atomic step list (Track B)

| # | Unit | Owner | Files | Size |
|---|---|---|---|---|
| B1 | Lightning-flag scanner: brightness-delta heuristic, write `flagged.json` per event dir | Jr | `/ganuda/services/sky_events/lightning_flagger.py` + systemd unit | 45 min |
| B2 | `/api/cameras/events?camera=X&days=N` endpoint, scan sky_events/ filesystem, return JSON metadata | Jr | `/ganuda/home/dereadi/sag_unified_interface/app.py` (extend) | 30 min |
| B3 | `MotionEventTimeline.js` reads `/api/cameras/events` on mount, renders 14d strip with thumbnail clicks | Jr | `/ganuda/sag_ui/src/components/MotionEventTimeline.js` + `pages/CamerasPage.js` | 1 hr |
| B4 | inotify watcher on `/ganuda/data/sky_events/`, on new dir post thumb to Slack `#sky-events` (and `#sky-lightning` if flagged) | Jr | `/ganuda/services/sky_events/slack_alerter.py` + systemd unit | 1 hr |
| B5 | Daily cron purger: `find /ganuda/data/sky_events -mindepth 1 -maxdepth 1 -mtime +14 -type d`, skip if `flagged.json` says interesting=true, rm -rf | Jr | `/ganuda/services/sky_events/retention_purger.sh` + cron | 20 min |

## Acceptance per unit

- **A1:** Partner sends `/glance traffic` to ganudabot; gets back JPG within 5s. Same for `/glance garage`, `/glance office_pii`. Bare `/glance` defaults to `traffic`.
- **B1:** Lightning_flagger runs over historical 2,235 events; writes `flagged.json` to those that score above threshold. Service stays running, processes new events as they land.
- **B2:** `curl http://localhost:4000/api/cameras/events?camera=traffic&days=14` returns JSON list with timestamp, frame_count, has_clip, flagged.
- **B3:** Loading `:4000/#cameras` shows live feeds AND timeline of last 14d. Click event → burst grid → click frame → full-size + MP4 link.
- **B4:** New event hitting sky_events/ produces a Slack post in `#sky-events` within 30s with thumbnail + caption. Flagged events also post to `#sky-lightning`.
- **B5:** After 14d, an unflagged event is deleted; a flagged event survives.

## Rollback
- A1: revert single file in derpatobot.
- B1-B4: stop systemd unit / revert file / no data loss.
- B5: stop cron, no further deletion. Already-deleted events not recoverable — but flagged exemption protects "cool" ones; retention is intentional.

## Bonus deferred to LMC follow-up (not tonight)
- Archive/delete `/ganuda/data/vision/` (132G of pre-Apr-11 single-shot orphan) — needs sign-off that it's not consumed by anything.
- `sky_events_storage_relocation` — move sky_events/ to /u + symlink for additional headroom (current 94% → would drop to ~50% post-relocation). Defer until after retention proves out; retention alone may make this unnecessary.
- Phase 2 lightning classifier (streak vs flash, ML model) — current B1 is brightness-delta heuristic only.
- Fire Guard sub-checks: partition >85%, single log >1G no rotation, snap-rootfs leak count.
