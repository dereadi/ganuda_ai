# KB: Job Search and Application Pipeline
**Date:** Mar 2 2026
**Status:** Active — Outreach Wave 2 sent, classification pipeline not yet running
**Author:** TPM

---

## Overview

This document captures the full state of the job search and application pipeline as of Mar 2 2026. The pipeline has two layers: outreach (manual + scripted) and tracking/classification (infrastructure built, not yet running). Wave 2 outreach has been sent. Gap: the tracking layer needs to be stood up so responses can be automatically classified and routed.

---

## Infrastructure

### Email Daemon
- **Script**: `/ganuda/email_daemon/gmail_api_daemon.py`
- **Auth**: OAuth 2.0, token stored at `~/.gmail_credentials/token.pickle`
- **Classifier**: `/ganuda/email_daemon/job_classifier.py`
- **Service name**: `cherokee-email-daemon.service` — NOT FOUND as a systemd unit. Daemon has not been deployed as a service.
- **Status**: Email sending works via Gmail API (used for outreach). Inbound classification pipeline not running.

### Job Research Scripts
- `/ganuda/jr_executor/job_research.py`
- `/ganuda/jr_executor/job_match_analyzer.py`
- **Research data directory**: `/ganuda/data/job_research/`
  - `source_hn_whoishiring.json` — scraped HN Who's Hiring thread data
  - `top_job_matches.json` — scored match output from analyzer

### Database Tables (bluefin PostgreSQL)
- **`email_classifications`**: Classifies incoming emails by category (interview, rejection, auto-reply, etc.). Currently EMPTY. Daemon not running.
- **`job_pipeline`**: Tracks applications and their status through the funnel. Currently EMPTY. Needs population from outreach records.

---

## Resume Inventory

| File | Location | Format | Status |
|------|----------|--------|--------|
| `Darrell_Reading_Systems_Architect_Resume_Mar2026.md` | `redfin:/ganuda/data/resumes/` | Skills-forward | CURRENT — use for applications |
| `Darrell_Reading_Systems_Architect_Dossier_v8.md` | `bmasass:/Users/Shared/ganuda/docs/` | Narrative masterpiece | Use for interviews |
| `Darrell_Eugene_Reading_Resume_Jan2026.md` | `bmasass:/Users/Shared/ganuda/docs/` | ATS-friendly traditional | Use for ATS portals |
| `Darrell_Eugene_Reading_Resume_MultiAgent_Dec2025.md` | `bmasass:/Users/Shared/ganuda/data/resumes/` | Multi-agent focus | STALE — do not use |
| GroupOne IT customized versions | `bmasass:/Users/Shared/ganuda/data/resumes/customized/` | Customized | Archived |
| `Darrell_Reading_Systems_Architect_Dossier_v6.md` | `sasass:/Users/Shared/ganuda/docs/` | Narrative earlier draft | Superseded by v8 |
| `resume_actual_facts_report.md` | `redfin:/home/dereadi/` | Verified facts | Reference only — Nov 2025 fact-check |

---

## Outreach Campaign Log

### Wave 1 — Feb 26 2026 (HN Who's Hiring Feb)
**12 personalized emails sent:**

| Company | Contact | Notes |
|---------|---------|-------|
| Charted Sea | Marc (direct) | Personalized to Marc |
| LiveKit | David (direct) | Personalized to David |
| Midpage | — | |
| TextQL | — | |
| FreightRoll | — | |
| Rad AI | — | |
| Office Hours | — | |
| Parts Order | — | |
| deepset | — | |
| Estuary | — | |

### Wave 2 — Mar 2 2026 (HN Who's Hiring March thread)
**8 emails sent via Gmail API.**
**Stored at**: `/ganuda/data/resumes/outreach_emails_mar2026.md`

| Company | Role | Location | Salary Range |
|---------|------|----------|-------------|
| Ford | Cloud SRE | REMOTE | — |
| FetLife | Head of Engineering | REMOTE | $182K–$272K |
| Radar Labs | SRE | REMOTE | — |
| Lithic | Senior SWE | REMOTE | $160K–$200K |
| OneChronos | Systems Engineer | — | — |
| Adobe | AI Agent Engineer | — | — |
| VLM Run | Infrastructure | — | $150K–$220K + equity |
| Tangled | Distributed Systems | REMOTE | — |

---

## Warm Leads (Active — Monitor Weekly)

| Company | Contact | Role | Status | Next Action |
|---------|---------|------|--------|-------------|
| PAM Transport | Emily Riley (RILEE@pamt.com) | Systems Administrator | Scheduling call | Follow up Mon Mar 3 2026 |
| America's Car-Mart | — | Solutions Architect, Rogers AR | Indeed match | Apply formally |
| Walmart | — | Distinguished SWE (?) | "Thank you for your interest" received | Monitor |
| Tyson Foods (via ZipRecruiter) | — | Lead Developer Procurement, NW Arkansas | Personalized match | Apply |

---

## Manual Web Applications Still Pending

These require browser-based form submission. Not yet submitted:

| Company | Role | URL |
|---------|------|-----|
| Deep Systems | Senior DevOps Engineer | https://jobs.gusto.com/postings/deep-systems-llc-senior-devops-engineer |
| AllSpice.io | (check careers page) | https://www.allspice.io/careers |
| Softmax | Software Engineer | https://softmax.com/jobs/softwareengineer |
| Ford | (formal portal — supplement email) | https://apply.ford.com/en/sites/CX_1/job/58080 |

---

## Top Job Match Analysis (from job_match_analyzer.py, Dec 2025 baseline)

| Role Category | Match Score | Rate/Salary Range |
|---------------|------------|-------------------|
| Multi-Agent Systems Developer | 83.3% | $150–$280/hr |
| AI Consultant / Contractor | 81.7% | $175–$350/hr |
| AI/ML Engineer — LLM Focus | 79.9% | $180–$300K/yr |
| Technical Architect — AI Systems | 79.7% | $200–$300K/yr |
| AI Infrastructure / MLOps | 78.5% | $160–$250K/yr |

These scores reflect the federation's differentiated profile: full-stack AI infrastructure, multi-agent orchestration, and operational systems at scale. These categories should drive targeting decisions.

---

## Outreach Pattern (What Works)

Each email should:
1. **Personalize to their tech stack** — reference specifics from their HN post
2. **Reference the HN thread** — shows you are in the community, not bulk-applying
3. **Bridge to federation experience** — frame the Cherokee AI Federation as proof of work, not a side project
4. **Link ganuda.us** — let the blog speak instead of attaching a resume
5. **Include phone + email in signature** — no attachments
6. **Be short** — 3–5 paragraphs, not a cover letter

---

## Gap Analysis and Next Steps

### Critical Gap: Email Classification Pipeline Not Running
The `email_classifications` and `job_pipeline` tables on bluefin are both empty. `cherokee-email-daemon.service` does not exist as a systemd unit. As responses begin arriving from Waves 1 and 2, there is no automated routing or tracking.

**What needs to happen:**
1. Deploy `gmail_api_daemon.py` as a systemd service (`cherokee-email-daemon.service`) on redfin or bluefin
2. Wire `job_classifier.py` to write classified results into `email_classifications`
3. Seed `job_pipeline` with Wave 1 and Wave 2 outreach records (company, role, date sent, status = "applied")
4. Define pipeline status states: applied → response_received → screening → interview → offer → rejected → ghosted

### Immediate Manual Actions (This Week)
- [ ] Follow up with Emily Riley (PAM Transport) — Mon Mar 3
- [ ] Submit 4 pending manual web applications (Deep Systems, AllSpice, Softmax, Ford portal)
- [ ] Apply formally to America's Car-Mart Solutions Architect role
- [ ] Investigate Tyson Foods Lead Developer Procurement (ZipRecruiter match)
- [ ] Seed job_pipeline table with all Wave 1 and Wave 2 records

### Next Wave Targeting
- NW Arkansas roles are high priority (America's Car-Mart, Tyson Foods). Local physical presence is a differentiator.
- Remote roles in AI infrastructure, multi-agent systems, and MLOps align to the 83% match category.
- Consider contractor/consulting outreach — highest $/hr ceiling and matches the federation's build-vs-buy differentiation story.

---

## Related Files

- `/ganuda/email_daemon/gmail_api_daemon.py`
- `/ganuda/email_daemon/job_classifier.py`
- `/ganuda/jr_executor/job_research.py`
- `/ganuda/jr_executor/job_match_analyzer.py`
- `/ganuda/data/job_research/source_hn_whoishiring.json`
- `/ganuda/data/job_research/top_job_matches.json`
- `/ganuda/data/resumes/outreach_emails_mar2026.md`
- `/ganuda/data/resumes/Darrell_Reading_Systems_Architect_Resume_Mar2026.md`
