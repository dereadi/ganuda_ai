# Jr Atomic: Sky Events — Lightning Flag (Phase 1 brightness-delta heuristic)

**Parent adapt plan:** `/ganuda/docs/lm_sky_events_review_adapt_plan.md` (Track B, B1)
**Trigger:** 717G accumulated sky_events with no curation; need to mark "interesting" events (lightning, fireball-like) so they're preserved when 14d retention runs.
**SP:** 2
**Assigned:** `it_triad_jr`
**Author:** TPM (Stoneclad)
**Blocks:** B5 (retention purger) — must land before purger runs in production.

## Objective

Build a service that scans each sky_events event directory, computes a brightness-delta heuristic across the burst frames, and writes a `flagged.json` file marking the event as `interesting=true` if it likely contains a lightning flash (or other bright transient). Service runs on existing events (one-shot backfill) AND continuously processes new events as they land.

## Files to create
- `/ganuda/services/sky_events/lightning_flagger.py` (the scanner)
- `/ganuda/config/systemd/sky-lightning-flagger.service` (systemd unit)

## Heuristic spec (Phase 1 — cheap, no ML)

For each event dir `/ganuda/data/sky_events/<ts>_<cam>/`:

1. Skip if `flagged.json` already present (idempotent).
2. Glob `burst_*.jpg`. If <10 frames, skip (incomplete event).
3. For each frame, compute mean luminance (use Pillow `Image.convert("L")` then numpy mean — fast, no OpenCV needed).
4. Compute median across all frames' means.
5. Find the max-luminance frame. Compute `delta = (max_lum - median_lum) / median_lum`.
6. If `delta > 0.50` (50% brighter than median) → flag as lightning candidate.
7. Write `flagged.json`:
   ```json
   {
     "interesting": true,
     "reason": "lightning_candidate",
     "max_delta": 0.74,
     "max_frame": "burst_0042.jpg",
     "median_lum": 38.2,
     "max_lum": 66.4,
     "scanned_at": "2026-04-25T22:30:00Z",
     "version": "phase1_brightness_delta"
   }
   ```
   If below threshold, write `flagged.json` with `interesting: false` so we don't re-scan. Same schema, different reason `"no_signal"`.

## Service shape

- Two modes:
  1. `--backfill` — walk all existing event dirs, process those without `flagged.json`. One-shot.
  2. `--watch` — `inotify_simple` (or pyinotify) on `/ganuda/data/sky_events/`. On new dir created with `clip.mp4` present (i.e. event finalized), run the heuristic.
- Default mode (no flag): backfill once then enter watch mode.
- Log to `/ganuda/logs/sky_lightning_flagger.log` with rotation (configure logrotate or use Python's RotatingFileHandler with 10MB cap). **Do not write unbounded logs** — that's how we got into the disk-full state in the first place.

## Systemd unit
```ini
[Unit]
Description=Sky Events Lightning Flagger
After=network.target

[Service]
Type=simple
User=dereadi
Group=ganuda-dev
ExecStart=/usr/bin/python3 /ganuda/services/sky_events/lightning_flagger.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

(TPM installs systemd unit per `feedback_adapt_phase_is_tpm_orchestration` — Jr writes the file content, TPM does the actual `cp` + `systemctl enable`.)

## Acceptance criteria

- [ ] `python3 lightning_flagger.py --backfill` runs without crash, processes all 2,235 existing event dirs
- [ ] After backfill, every event dir has a `flagged.json` (either interesting=true or false)
- [ ] Some non-zero count of events tagged `interesting=true` (sanity check — Apr 25 storm tonight should have produced some; if 0 across all 2235, threshold is wrong)
- [ ] Watch mode picks up a fresh event within 60s of `clip.mp4` appearing
- [ ] Service log file does NOT grow unbounded — verify rotation is in place
- [ ] No GPU dependency — must run on CPU only (this is redfin, GPUs are for Council specialists)

## Verification (Jr runs)

```bash
# Backfill smoke test on 5 dirs
python3 /ganuda/services/sky_events/lightning_flagger.py --backfill --limit 5

# Check output
for d in $(ls -td /ganuda/data/sky_events/*/ | head -5); do
  echo "$d:"
  cat "$d/flagged.json" 2>&1 | head -10
done

# Histogram of flagged across all events
find /ganuda/data/sky_events -name flagged.json -exec grep -l '"interesting": true' {} \; | wc -l
find /ganuda/data/sky_events -name flagged.json | wc -l
```

## Out of scope (do NOT do these here)
- Real lightning classifier (Phase 2 — separate ticket later)
- Streak vs flash distinction (Phase 2)
- NASA Skyfall API cross-reference (Phase 2)
- Slack alerts on flagged events (B4 — separate ticket)
- Retention deletion (B5 — separate ticket, depends on B1)

## Notes for Jr
- Threshold `0.50` is a starting guess. If backfill produces 0 flagged or 90%+ flagged, threshold needs tuning. Report the histogram and TPM will tune.
- Don't over-engineer. Pillow + numpy is enough. No OpenCV, no torch.
- Pillow can read JPG without decoding all 200 frames at full res — use `Image.open(path).convert("L").resize((100, 100))` to keep CPU low. We're computing means, not pixel-level analysis.
- Idempotency matters — if service restarts mid-backfill, it must resume cleanly (skip dirs that already have flagged.json).
