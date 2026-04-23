# Telemetry / Phone-Home Policy — Sovereign by Default

**Closes kanban duyuktv_tickets #2069** (Crawdad-tagged, P1, 3 SP).

**Source:** Apr 19 2026 grep audit of `/ganuda/scripts`, `/ganuda/daemons`, `/ganuda/lib`, `/ganuda/services`, `/ganuda/jr_executor`, `/ganuda/backend`. Vendored 3rd-party packages (site-packages, node_modules, vendor/) excluded.

## Policy

> The federation defaults to sovereign — no service phones home, sends telemetry, or transmits data to an external endpoint without explicit Council approval and an entry in this registry.

Every external HTTP/HTTPS destination touched by federation code MUST be:
1. **Justified** — what the call does, what data leaves the node, who consumes it
2. **Optional** — a sovereignty toggle that disables the call (env var or config) MUST exist
3. **Logged** — calls observable in journal/structured logs
4. **Audited** — listed in this registry, reviewed quarterly

Anything not listed here that gets discovered is a policy violation and a kanban ticket gets filed automatically.

## Federation external destinations (Apr 19 audit)

| Destination | Federation files | Purpose | Data leaving node | Sovereignty risk | Status |
|---|---:|---|---|---|---|
| `api.telegram.org` | 29 | Council bot, alerts, notifications | Message text, chat IDs | LOW (Partner-controlled bot/group) | Approved |
| `api.openai.com` | 9 | Fallback LLM (Gemini-ring redundancy added Mar 2026) | Prompt + completion text | MEDIUM (provider sees content) | Approved (toggle: `OPENAI_API_KEY` unset = disabled) |
| `huggingface.co` / `hf.co` | 9 | Model weight downloads | Model identifier; no user data | LOW (public HF models) | Approved |
| `api.anthropic.com` | 3 | Claude API (Council subagents, Brain-A on cloud-fallback path) | Prompt + completion | MEDIUM (provider sees content) | Approved (toggle: `ANTHROPIC_API_KEY` unset = disabled) |
| `api.github.com` | 3 | Repo operations (clone, issue refs, release fetches) | Repo paths, public-key fingerprint | LOW | Approved |
| `linkedin.com` (read-only) | 2 | Editorial reference parsing for Deer's content pipeline | None outbound | LOW | Approved |
| `hooks.slack.com` | 2 | Coyote bot + Eagle-Eye pulse messages | Alert text | LOW (Partner-controlled workspace) | Approved |
| `generativelanguage.googleapis.com` | 1 | Gemini API (added Mar 2026 per audit, ring-redundant with OpenAI/Anthropic) | Prompt + completion | MEDIUM | Approved (toggle: `GEMINI_API_KEY` unset = disabled) |
| `cloudflare.com` | 1 | Tunnel/cert ops | DNS records, cert metadata | LOW | Approved |
| `*.amazonaws.com` (via anker-solix-api) | 0 federation, all in 3rd-party lib | Anker IoT (Solix battery) telemetry — but this is the IoT library calling Anker's AWS-hosted endpoints | Battery state, location | MEDIUM (Anker as 3rd party) | Approved (Partner uses Solix, opt-in by deploying solix-monitor.service) |

**No usage detected of:** sentry.io, posthog, amplitude, datadog, newrelic, bugsnag, stripe, mailgun, sendgrid, twilio, substack-write-API, AWS direct.

## Implicit/transitive concerns flagged

- **`anker-solix-api` (3rd-party)** — vendored library with 201 references to amazonaws.com endpoints. The library calls Anker's cloud, which is AWS-hosted. Sovereignty risk depends on what Anker SEES — battery state, charge cycles, location. Mitigation: solix-monitor.service is opt-in; remove the unit if Solix not in use.
- **`yt-dlp` (vendored in research/transcript pipelines)** — references thousands of media-site domains (yt-dlp's job). Only outbound when actively transcribing a URL. Not a passive phone-home but an active fetch. Acceptable.
- **`pip install` / package fetches at deploy time** — pulls from PyPI/conda/HuggingFace. Standard build-time, not runtime.

## Recommended additions (none today, future hooks)

If/when added: each requires a Council vote logged to thermal memory + entry here.
- Substack write-API for Deer auto-publish (today: drafts only, Partner reviews + posts manually)
- Federated learning / metrics aggregation across community land-trust nodes
- Any product analytics on SAG/Ganuda-Shield/Moltbook customer-facing tiers

## Enforcement

- **Quarterly audit** — repeat this grep, diff against registry, file ticket per delta
- **CI hook** — pre-commit grep for new external endpoints in code being committed; block if not in registry
- **Drift alarm** — extend the `secrets-drift.timer` pattern to also detect new outbound endpoints in `journalctl` over the last hour

## Status update

Update `duyuktv_tickets` #2069 status: `completed`, resolution_notes: "Synthesized via Apr 19 TPM-direct work. Policy + registry in /ganuda/docs/telemetry_policy.md. Council policy: sovereign by default; quarterly audit cadence; CI hook + drift alarm recommended for next sprint."
