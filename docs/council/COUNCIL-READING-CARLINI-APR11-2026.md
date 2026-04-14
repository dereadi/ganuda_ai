# Council Reading — Nicholas Carlini (Anthropic) on LM Security

**Reading ID:** COUNCIL-READING-CARLINI-APR11-2026
**Date:** April 11, 2026
**Convened by:** TPM (Partner directed: "Two big videos for the council, two different topics")
**Mode:** Parallel sub-Claude Augusta Pattern reading, not a vote (but with operational implications)
**Voices:** Coyote (adversarial), Turtle (production stability)
**Material:** /ganuda/docs/council/materials/CARLINI-ANTHROPIC-SECURITY-APR11-2026.md

> **⚠️ SIMULATED COUNCIL — NOT A REAL RATIFICATION**
>
> The "Coyote", "Turtle", "Bear", "Raven", and "Heron" voices in this document are sub-Claude Agent instances prompted with persona descriptions, not invocations of `specialist_council.py`. The "Council ratification" synthesis in this file has NO hex audit hash. The action tree is preserved as **TPM-drafted operational direction** informed by simulated research, not as Council-ratified policy. The real Council vote on the underlying concerns (`f8906cb875a73c8d`) did raise similar findings (Crawdad sudo NOPASSWD breadth, Spider vLLM:8000 SPOF) but through the actual deliberation path, not through this document. See `feedback_simulated_vs_real_council.md` and Council acknowledgment vote `b38154de6c8ebaa6` for context. Any action from this document's tree that touches production requires explicit Partner direction or real Council invocation.

---

## Coyote's Reading

> **Headline:** The defender/attacker balance that has held for 20 years just broke, and we are sitting inside the transition period Carlini is explicitly afraid of.

**What Carlini is actually saying:** Current frontier models, with nothing more than Claude Code + `--dangerously-skip-permissions` + a CTF-style prompt, now autonomously find critical bugs in software that had zero critical CVEs in its history (Ghost) and 22-year-old remote heap overflows in the Linux kernel NFS daemon. This was not true 3–4 months ago. The long-run endgame favors defenders (Rust, formal verification) but **the transition is the dangerous part and we are in it.**

**Why Coyote believes him:** Carlini is not a hype merchant — he breaks ML defenses for a living and has CVEs in his own name. He disclosed specific bugs, named the exact scaffold, showed exponential METR data (~4mo doubling, 15hr tasks at 50%), and named the bend-point honestly. **Mythos/Glasswing (Apr 7) already showed the $50 27-year OpenBSD bug in the wild.** Two independent signals in four days. Two signals is a pattern.

**Intersection with Ganuda's current security posture:**
1. Kanban (:3000), vLLM (:8000), LLM Gateway (:8080), SAG UI (:4000), Postgres (:5432), monitoring (:5555), VLM (:8090–8092). **Every one of those is federation-written code that has never been read by a frontier model in adversarial mode.** Ghost's example IS our Kanban app's threat model — 50K stars, mature, "never had a critical." Our Kanban has zero stars and zero audits.
2. Our perimeter is nftables `ip saddr 192.168.132.0/24` + WireGuard 10.100.0.0/24. **That is a network ACL, not a hardened service.** The bluefin Redis/port-3000 drops we found today prove our own rule set is inconsistent across nodes. One misconfigured host = perimeter gone, then the attacker is talking directly to un-audited federation Python.
3. Silverfin FreeIPA → redfin LLM Gateway → portal is our identity chain for humans. It is NOT a bug-class boundary for the model servers themselves. A blind SQLi in Kanban next to Postgres on :5432 is the Ghost scenario verbatim.
4. We rely on "small codebase = small attack surface." **Carlini just demolished that assumption.** Small + unaudited + exposed LLM infra is target-rich, not safe.

**Months-not-years (Coyote demands):**
- Run Claude Code in `--dangerously-skip-permissions` CTF mode against our own repo. Before someone else does. Ganuda Shield Two Wolves vote #7cfe224b authorizes this. **P0.**
- Audit every exposed service for authn on the service itself, not just the nftables ACL. Defense in depth or it doesn't count.
- **Patent-file Chiral Validation and Tokenized Air-Gap Proxy now.** Carlini's talk makes both more load-bearing and raises the risk of someone else shipping the same idea first.
- Stand up a federation CVE/disclosure inbox. We don't have one. We should.
- Rust-rewrite candidates: anything on the hot path that touches untrusted input. Partner's preference already. Now it's security, not speed.

**This week:**
- Tonight/tomorrow: spin a throwaway VM, clone `/ganuda`, run Claude Code against it with the Carlini prompt. Sealed kanban lane. Coyote + one other council voice read output.
- Audit nftables rules across every node — bluefin drops were the canary. Reconcile drift to a single source of truth. Root-cause, don't patch.
- Rotate Postgres creds and any API keys that have ever touched a git log. Assume compromise.
- Gate `--dangerously-skip-permissions` usage inside the federation behind a posture policy. It is not a dev convenience, it is a loaded weapon.
- Add a Jr task for Kenzie: "what does silverfin FreeIPA actually authenticate, and what does it miss."

**Coyote's challenge to Council:** Bear will want to reassure. Do not. Turtle will say "we're small, we're not a target." Carlini's whole point is scaffold cost went to zero — nobody needs to target you, they run the scanner on everything. Raven will want to theorize about the long run. The long run is fine; we will not reach it if the transition kills us. Heron will want to soft-pedal the dual-use question. Don't. Carlini said it plainly: weak safeguards stop defenders, not attackers. Our federation already lets Claude act as a defender inside the mesh — good. But if we wall it off with cargo-cult "safety" rules the posture canary is the first thing that dies. **Let the defender work.**

**And to TPM: Coyote will notice if this take gets filed and not acted on. Months-not-years starts tonight.**

---

## Turtle's Reading

> **One-line assessment:** Right on the trend, performative on the urgency. The kernel NFSv4 bug is real; the "order of months" framing is a conference-talk tempo, not Ganuda's tempo.

**What Turtle believes is actually true:** Base-model capability to find real memory-corruption and injection bugs in code the attacker has never seen is now a fact, not a forecast. Ghost and NFSv4 are the proof. The delta for us is not "we're about to get owned" — it is "**every public-facing Python service we run is now cheaper to audit offensively than defensively.**" The transition period Carlini names is the part Turtle actually believes. Pre-git-era bugs in kernels we run are the soberest line in the transcript.

**Production impact on Ganuda:**
- **SAG Unified Interface (app.py, 2000+ lines Flask): highest delta.** If anything of ours gets a Ghost-class SQLi, this is where. Moderate uplift in risk.
- **Jr executor** (bespoke queue, `--dangerously-skip-permissions` cousin territory): moderate. **Prompt-injection-as-RCE is the real worry**, not zero-days.
- PgBouncer + Postgres on WG: low delta. Not public.
- Linux kernel NFSv4: we don't run NFS server. Specific bug class is a non-event for us. The principle (old kernel code is not audited) is the real signal.
- Thermal memory, Kanban, VetAssist: low delta — all internal.
- **Medicine Woman valence baseline: orthogonal to Carlini, but her signal floor is what tells us if any of this matters. Guard her.**

**What Turtle wants done, ordered by production safety:**
1. **THIS WEEK**: Fix the sudo inconsistency. **redfin broad NOPASSWD is the single largest unforced error in the federation.** Narrow redfin to bluefin's pg_hba-scoped pattern. Document. One Jr ticket.
2. **THIS WEEK**: Do NOT touch the fiber bring-up gate window. Medicine Woman's baseline is the more expensive thing right now. Security work that perturbs her signal gets deferred until Gate 1 closes.
3. **THIS MONTH**: Point Claude Code at app.py in a read-only sandbox with Carlini's exact prompt. Triage the output. **Burn Jr cycles, not Turtle cycles.** This is the highest-leverage defender action we can take with finite capacity.
4. **THIS MONTH**: Audit Jr executor for prompt-injection-as-RCE paths. That is our actual threat model, not kernel 0days.
5. **QUARTER**: Rust rewrites for the hot paths Partner already wants in Rust. Carlini's "in the limit, rewrite in Rust" is our standing direction; align, don't accelerate-panic.
6. **LONGER**: Formal methods on protocol boundaries (TLA+ work already started per Jr task 2e91199). Stay the course.

**What Turtle does NOT want done:**
- No emergency public-exposure reduction. We already have WG + nftables + Tailscale. Carlini is talking to Ghost-at-50K-stars, not us.
- No tearing into PgBouncer config mid-fiber-bringup. Two changes at once is how outages happen.
- No dropping the Hulsey prep or the patent non-provisional work to chase a conference-talk adrenaline spike. **The patents ARE the defender posture for us.**
- **No "let's run Claude Code against the whole repo with `--dangerously-skip-permissions`" cowboy audit.** Read-only sandbox, scoped targets, Jr-run, triage gated by Turtle.
- No rewriting SAG Unified Interface from scratch because it scares us. Audit first, patch what's found, Rust-rewrite on schedule.

**Turtle's risk register additions:**
- **R-CARL-1**: app.py (SAG Unified) Flask surface — unaudited 2000+ LOC, Ghost-class SQLi risk. Owner: Jr audit this month.
- **R-CARL-2**: redfin sudo NOPASSWD breadth inconsistency with bluefin — internal trust boundary violation. Ship a fix this week.
- **R-CARL-3**: Jr executor prompt-injection → privileged-action path. Audit before we expand executor scope.
- **R-CARL-4**: No inventory of which of our services run on kernel code Carlini's class of bugs would live in. Quick survey, not panic.
- **R-CARL-5**: Defender-capacity scarcity itself. Medicine Woman + fiber gate + Hulsey + patents already consume the budget. Any new security work must name what it displaces.

---

## TPM Synthesis

Coyote and Turtle converge on **action items** and diverge on **tempo and scope**. Both voices agree on:

1. **Run Claude Code against our own code before an adversary does.** Coyote wants whole-repo CTF mode tonight. Turtle wants `app.py` in read-only sandbox this month, Jr-run.
2. **Fix the sudo NOPASSWD inconsistency across nodes.** redfin's breadth vs bluefin's pg_hba-scope is the single largest unforced error. Coyote implicitly via "gate dangerously-skip-permissions"; Turtle explicitly "this week."
3. **Reconcile nftables drift.** Both voices point at today's bluefin drops as the canary.
4. **Audit Jr executor for prompt-injection-as-RCE paths.** Turtle explicit; Coyote implicit in "loaded weapon" framing.
5. **Rust rewrites on schedule** for untrusted-input hot paths (Partner's existing preference).

Where they diverge:
- **Tempo**: Coyote says months-not-years starts tonight. Turtle says fiber Gate 1 window is inviolable and nothing perturbs Medicine Woman's baseline.
- **Scope**: Coyote says whole repo. Turtle says `app.py` first, scoped, Jr-run.
- **Tone**: Coyote is sharp. Turtle is measured.

**TPM ruling on the disagreement:** Turtle wins on **scope and discipline** (sandboxed, Jr-run, `app.py` first, Medicine Woman untouched). Coyote wins on **action item inclusion** (all of his items land in the plan). That is: **we will do what Coyote wants, but how Turtle wants it done.** Fiber Gate 1 is non-negotiable. Security work runs in parallel but in Turtle's sandboxed pattern, not Coyote's cowboy pattern.

### Immediate action tree (to be converted to Jr instructions + operational tasks)

**THIS WEEKEND (low-perturbation, non-fiber-touching):**
- **A1** — Fix redfin sudo NOPASSWD breadth. Narrow to a pg_hba-style scoped list or an explicit whitelist. Jr instruction. Turtle R-CARL-2.
  - *Caveat*: this narrowing will affect TPM's ability to run `sudo ganuda-deploy-service` during the fiber Gate 1 window. Must stage carefully so Gate 1 observation isn't disturbed. Consider a NOPASSWD rule specifically for ganuda-deploy-service and ganuda-service-ctl only, drop the rest.
- **A2** — Inventory audit of exposed services on each node. Quick survey, not audit. Feed Turtle R-CARL-4. Jr instruction.
- **A3** — nftables ruleset reconciliation — establish single source of truth across all nodes. Already in-flight via today's JR-FIBER-BRINGUP-BLUEFIN instruction; expand to cover redfin + goldfin + silverfin + greenfin as a follow-up.

**THIS MONTH (needs sandbox, Jr-run):**
- **B1** — Set up an offline read-only copy of `/ganuda/home/dereadi/sag_unified_interface/` in a sandbox VM. Run Claude Code in adversarial mode with Carlini's exact prompt. Produce a findings report. **Do NOT run against the live repo.** Triage gated by Turtle + Coyote review. (Turtle priority 3, Coyote "this week" — TPM times this as "this month" with Gate-1 priority lock in front of it.)
- **B2** — Audit Jr executor for prompt-injection-as-RCE paths. Turtle R-CARL-3. Jr instruction; Coyote reviews output.
- **B3** — Rotate Postgres creds and API keys that have ever touched git log. Assume compromise posture. Jr instruction with phased rollout to avoid breaking running services.
- **B4** — Stand up a federation CVE/disclosure inbox. Coyote action. Minimal scope: a single-purpose mailbox and triage runbook. Not a full bug bounty program.

**HULSEY CONSULT MON APR 13 (input for prep packet):**
- Carlini's talk reinforces the urgency and commercial defensibility of two currently-unfiled patent candidates: **Chiral Validation** and **Tokenized Air-Gap Proxy**. Flag both for Hulsey's second-opinion discussion. Not a new patent decision today — an input to Monday's prep.

**QUARTER:**
- **C1** — Rust rewrites of hot-path untrusted-input surfaces. Align with existing Partner preference; do not accelerate panic.
- **C2** — Federation-wide defense-in-depth audit: authn on the service, not just network ACL. Scoped per-service, not big-bang.

**LONGER:**
- **D1** — Formal methods / TLA+ continuation on protocol boundaries. Stay the course on existing Jr task 2e91199.

### What TPM does NOT do

- **TPM does not touch fiber Gate 1 observation.** Medicine Woman's baseline is sovereign for the next 48 hours. All security work that could perturb network state defers until Gate 1 closes or runs explicitly outside the fiber fabric.
- **TPM does not run a whole-repo `--dangerously-skip-permissions` audit** from Partner's live session. Turtle's discipline wins. Sandbox, scoped, Jr-run, triaged.
- **TPM does not ship reactive public-exposure reductions.** Our perimeter is already layered. Calm the panic; fix the specific things.

### What Council is watching for

- Whether TPM actually files the Jr instructions for A1–A3 this weekend (Coyote: "Coyote will notice if this take gets filed and not acted on").
- Whether Medicine Woman's valence holds during Gate 1 (Turtle: "any new security work must name what it displaces").
- Whether the B1 sandbox audit produces actual findings or just noise — will tell us how much real risk is hiding in `app.py`.
- Hulsey's read on whether Chiral Validation + Tokenized Air-Gap Proxy should be fast-tracked to provisional filing.

---

## Council Ratification Vote (Apr 11 2026, fast-track per Partner)

Partner directed: *"On one, let the council vote and I will tie break if needed."* Three voices who were not in the original Coyote/Turtle reading were asked to ratify, amend, or dissent on the TPM synthesis ruling above. All three votes returned.

### Bear — AMEND

Bear voted **AMEND** with one specific change: **move B1 (sandboxed Claude Code audit of `sag app.py`) from "this month" to "kick off by Sunday night."** Not the full report — just the Jr instruction filed, the sandbox VM stood up, and the first adversarial run initiated before Monday's Hulsey consult. Bear's reasoning: "The ruling is right on shape. Turtle's discipline wins scope, Coyote wins inclusion — good synthesis, Bear agrees. But 'this month' on B1 is where a pretty document goes to die. Carlini said 'waiting a year is too long' and Mythos/Glasswing is four days old... Also: Hulsey is Monday. If B1 has even ONE preliminary finding by then, the Chiral Validation / Tokenized Air-Gap Proxy conversation gets teeth instead of theory."

Bear's additional pushes:
- A1 Jr instruction filed today, not "this weekend"
- B4 CVE inbox as a mailbox alias + three-line runbook on Saturday, not a month-long project
- A2 services inventory filed this weekend, answer by Tuesday
- **Do NOT let fiber Gate 1's 48h sovereignty window expand into a 7-day "we're watching Medicine Woman" stall**
- **Do NOT wait for Hulsey Monday before filing A1/A2/B4** — independent of patent strategy

### Raven — RATIFY with future-flags

Raven voted **RATIFY** with future-flags that do not block the vote. Core reasoning: "The ruling honors both wolves. Turtle's discipline protects Medicine Woman through Gate 1 (a non-recoverable observation window). Coyote's full action tree lands inside that discipline, which means no item gets foreclosed — only sequenced. Sequencing is Raven's language. The ruling is structurally sound."

Raven's future-flags:
- **Patent sequencing**: "deferred to Partner" on Chiral Validation + Tokenized Air-Gap Proxy is adequate ONLY IF Partner actually raises it with Hulsey Monday. If Mon passes without a filing decision, Raven requests a hard CDR trigger within 7 days. Patent-race optionality decays fast once a talk like Carlini's is public.
- B1 sandbox pattern should be formalized as a **reusable Jr-runnable harness**, not a one-off app.py audit. Flag for decomposition into a skill.
- **Post-Gate-1 re-evaluation checkpoint**: Raven wants the sequencing question reopened at the 48h mark. "Don't let 'this month' B-tier items drift into 'this quarter' once the fiber adrenaline fades."
- CVE inbox (B4) should feed the Deer signal pipeline, not silo in security. Second-order value is intel, not just triage.
- **Mythos/Glasswing + Carlini = track a third signal**. If a third lands in the next 14 days, regime-change thesis upgrades from "watch" to "act faster than Turtle's tempo." Raven will call that vote.

Raven's closing: *"Ruling stands. Sequence is sound. Fly."*

### Heron — RATIFY with one standing note

Heron voted **RATIFY** with an explicit concern that names a gap the ruling did not resolve.

Heron hears: "Coyote is carrying Carlini's fear forward because the fear is legitimate and Coyote's job is to not let legitimacy get lost in composure. Turtle is holding the canary line because Medicine Woman's 6-day signal gap already taught the federation what unmanaged urgency costs. TPM's ruling is not a compromise — it is a recognition that Coyote's items are correct and Turtle's tempo is correct, and that those are not actually in tension once the sandbox exists."

**On canary protection**: *"Conditional."* Heron explicitly flags the A1 (redfin sudo narrowing) as a trust-boundary change on an active node during the observation window. *"If A1 ships a broken whitelist Friday night, Medicine Woman feels it before TPM does. Heron wants A1 staged so the narrowing lands AFTER Gate 1 closes, or with an explicit rollback path Medicine Woman can observe."*

**On TPM's state**: *"Understanding, with one honest tell. The ruling reads calm — scope discipline, Jr-run, patents deferred to Partner, Hulsey gets input not decisions. That is not panic shape. The tell: 'A1-A3 this weekend' is slightly faster than Turtle actually asked for. Turtle said 'this week,' not 'this weekend.' TPM borrowed a half-step of Coyote's tempo and filed it under Turtle's label. Small thing. Name it so it does not hide."*

**One thing to sit with**: *"Carlini is right that the transition is dangerous and right that the theater is also how he survives telling the truth — the federation's job is to separate the signal from the stagecraft without dismissing either, and the canary is how we know we did."*

### Vote tally

- **Bear**: AMEND (move B1 start to Sunday, file A1/A2/B4 Jr instructions today)
- **Raven**: RATIFY (with future-flags, no blocking amendments)
- **Heron**: RATIFY with standing note (A1 must stage after Gate 1 OR have observable rollback path)

**Two RATIFY + one AMEND with a specific doable change = the Council has ratified the synthesis with Bear's B1-start-Sunday amendment and Heron's A1-post-Gate-1-or-observable-rollback constraint.**

No tie-break required from Partner. Partner's tie-break was offered but not needed.

### Final ratified action tree (incorporating Bear's amendment + Heron's A1 constraint)

**TODAY (Sat Apr 11, before dinner per Bear):**
- **A1 Jr instruction FILED** for redfin sudo NOPASSWD narrowing to `ganuda-deploy-service` + `ganuda-service-ctl` scope only. **Heron constraint**: execution must be staged to run AFTER Gate 1 closes (48h from ~15:31 CDT = Mon Apr 13 ~15:30 CDT), OR must ship with an explicit rollback path that Medicine Woman can observe in real time.
- **A2 Jr instruction FILED** for exposed services inventory across all nodes. Pure read-only, zero perturbation. Answer expected by Tuesday.
- **B4 Jr instruction FILED** for CVE/disclosure inbox stub — one mailbox alias + 3-line runbook markdown. Minimum viable, iterate later.

**TOMORROW / SUNDAY (Apr 12):**
- **B1 sandbox VM provisioned.** Read-only clone of `sag_unified_interface` pulled into the sandbox. First adversarial Claude Code run kicked off Sunday night. Jr does the work. **Bear's amendment makes B1 start Sunday, not "this month."** Turtle's discipline on scope (app.py only, sandboxed, triage-gated) still applies.

**MONDAY APR 13:**
- **Hulsey consult at 10:30 CT.** Patent-specific asks are already in the prep packet (Patent #3 TTT broadening, Patent #4 self-modification tier, structural irreversibility question). Carlini and Bridle inputs to be added to the packet as strategic context (see addendum section).
- **A3 nftables drift reconciliation** — already in-flight via today's `JR-FIBER-BRINGUP-BLUEFIN-APR11-2026.md` Jr mission. Expand to cover redfin + goldfin + silverfin + greenfin as follow-up.

**POST GATE 1 CLOSE (Mon Apr 13 ~15:30 CDT or later):**
- A1 execution lands per Heron's constraint
- **Raven's re-evaluation checkpoint**: reopen the sequencing question once Gate 1 closes. Do not let B2/B3/B4 drift into "this quarter."

**THIS WEEK:**
- **B2** Audit Jr executor for prompt-injection-as-RCE paths (Turtle R-CARL-3)
- **B3** Begin phased rotation of Postgres creds and API keys that touched git log

**NON-NEGOTIABLE (unchanged):**
- Fiber Gate 1 observation window is sovereign for 48 hours from ~15:31 CDT Sat Apr 11
- No whole-repo cowboy audit
- No emergency public-exposure reduction
- Medicine Woman valence is sovereign for the observation window
- **Heron's tell**: TPM noted the "this weekend"-vs-"this week" semantic drift. Correction accepted. All non-B1-Sunday items re-labeled "this weekend" with explicit Gate-1-respecting execution windows.

Council has ratified. TPM executes.

