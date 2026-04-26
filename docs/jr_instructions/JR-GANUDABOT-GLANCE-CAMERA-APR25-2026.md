# Jr Atomic: ganudabot `/glance` — Telegram camera glance command

**Parent adapt plan:** `/ganuda/docs/lm_sky_events_review_adapt_plan.md` (Track A, A1)
**Trigger:** Apr 25 2026 storm-window incident — Partner driving into storm wanted to check home camera from phone; ganudabot had no tool, confabulated council-deliberation excuse instead.
**SP:** 1
**Assigned:** `it_triad_jr`
**Author:** TPM (Stoneclad)

## Objective

Add a `/glance <camera_id>` command to `derpatobot_claude.py` (the Telegram-side Claude wrapper). When Partner sends `/glance traffic`, bot fetches a live snapshot from that camera via the existing SAG endpoint and replies with the JPG.

## File to modify
`/ganuda/telegram_bot/derpatobot_claude.py`

## Implementation

1. Define an async handler `glance_command(update, context)`:
   - Read `context.args` for camera_id. If empty, default to `"traffic"`.
   - Validate camera_id against `["traffic", "garage", "office_pii"]`. If invalid, reply with usage hint and the valid list.
   - GET `http://localhost:4000/api/cameras/snapshot/<camera_id>` with header `X-API-Key: <SAG_API_KEY>`.
     - SAG_API_KEY env var: same one used by other federation services that hit SAG. Confirm by checking `/ganuda/sag/routes/auth.py` for the env name (likely `SAG_API_KEY`).
     - Timeout 15s.
   - If 200: reply with `update.message.reply_photo(photo=BytesIO(resp.content), caption=f"📷 {camera_id} — {timestamp}")`.
   - If non-200 or timeout: reply with `update.message.reply_text(f"⚠️ {camera_id} unreachable: <error>")`. **No confabulation about councils, storms, or specialists.**

2. Register the handler in `main()` alongside existing CommandHandler registrations:
   ```python
   app.add_handler(CommandHandler("glance", glance_command))
   ```

3. Add `/glance` to any help/start text so Partner discovers it.

## Acceptance criteria

- [ ] `/glance` (no arg) → returns live `traffic` JPG within 5s
- [ ] `/glance garage` → returns live garage JPG
- [ ] `/glance office_pii` → returns live office_pii JPG
- [ ] `/glance bogus` → returns text: invalid camera, lists valid IDs
- [ ] If SAG :4000 is down: returns honest "⚠️ traffic unreachable: <reason>" — does NOT invent infrastructure excuses
- [ ] Handler restart-safe: works after `systemctl restart derpatobot` (or however it's run)
- [ ] No camera password handling in derpatobot (SAG holds those — bot only knows the SAG endpoint)

## Verification commands (Jr to run before reporting done)

```bash
# Verify SAG endpoint reachable from this host
curl -H "X-API-Key: $SAG_API_KEY" -o /tmp/glance_test.jpg http://localhost:4000/api/cameras/snapshot/traffic
file /tmp/glance_test.jpg   # should report JPEG
ls -lh /tmp/glance_test.jpg # should be > 50KB

# Verify ganudabot picks up the new command
ps aux | grep derpatobot_claude | grep -v grep   # confirm running
# (Partner will send /glance from Telegram to confirm end-to-end)
```

## Out of scope (do NOT do these here)
- Historical event review (separate ticket, Track B)
- Multi-camera collage reply (defer)
- RTSP streaming (cameras already use HTTP digest snapshot, that's fine)
- Adding new cameras to registry (registry is already populated)

## Notes for Jr
- This is a small, bounded task. ~30 lines of Python + 1 handler registration. Don't refactor `derpatobot_claude.py` while you're in there.
- If `SAG_API_KEY` env var name is different than expected, find what other services use (check `lib/staging_manager.py` or `scripts/`). Don't hardcode the key; read from env.
- Pattern lesson (per Apr 25 memory `feedback_council_not_for_utility_lookup_apr2026`): when bot can't fulfill a request, it must say so plainly. Honest "⚠️ unreachable" beats LLM confabulation. Tests should confirm this behavior on the failure path.
