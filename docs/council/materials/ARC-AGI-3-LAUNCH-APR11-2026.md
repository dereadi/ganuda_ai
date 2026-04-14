# ARC-AGI-3 Launch — ARC Prize Announcement — Transcript for Council deliberation

**Context:** Launch event for ARC-AGI-3 benchmark and ARC Prize 2026 ($2M competition). Speaker is an ARC Prize lead (likely Greg Kamradt based on framing). Followed by a fireside with Francois Chollet and Sam Altman moderated by DD Doss (Menlo Ventures).
**Date captured:** April 11, 2026 (Saturday)
**Filed by:** TPM at Partner's direction — "I have another video that the council will find quite interesting"

---

## Speaker's opening framing

> "If you're in this room, you likely care about where the frontier is going... that frontier is pointing towards artificial intelligence that is able to learn just like a human. Or to put another way, the frontier is general intelligence."

**ARC Prize's definition of general intelligence** (load-bearing):

> "We believe that general intelligence is not just a set of skills. So it's not how well you do at any one skill, but it's more the meta aspect. It's your ability to learn new skills. That's the important part — is the learning piece."

> "Despite what the headlines would lead you to believe, we do not yet have AGI. And we can say this with certainty because there's still a gap between what humans can do and what AI can do."

## ARC Prize's operating method

- **Measurement tool** — ARC AGI as a public sensemaking tool for where the frontier is
- **Target tool** — a benchmark that incentivizes new ideas to beat it and brings them into the open domain
- **Principled stance**: squarely focused on problems humans can do but AI cannot. "Direct comparison to the only existence proof of general intelligence you have — humans."
- **Why a series of benchmarks**: not moving goalposts — the goalpost is AGI. There can only be a finite number of ARC AGI benchmarks before the human–AI gap closes.
- **Falsifiable claim**: "when we can no longer come up with problems that humans can do and AI cannot, for all intents and purposes we have AGI at that point, and that is how we will know when AGI is here."

## What each prior benchmark signaled

- **ARC-AGI-1 (2019, pre-LLM, pre-scale)**: 5 years of minimal progress despite scaling. **First jump = December 2024 with OpenAI o3** — ARC-AGI-1 was the signal for the reasoning paradigm taking off.
- **ARC-AGI-2 (~year ago)**: slow progress initially, then **next jump when agentic coding took off** — humans giving more autonomy to agents ("used to be humans needed to give over 50% of control; now they give 50%").
- Pattern: each benchmark has become the signal for the next capability regime-change.

## ARC-AGI-3 — the announcement

> "With V1 and V2, we gave a static puzzle to AI and we asked can you solve it? But with V3, we put AI inside of an interactive environment and ask, can you figure it out on your own and by yourself?"

**Scale and construction:**
- Hundreds of games, **nearly 1,000 different levels**
- **Every game handcrafted by a human** — no procgen
- **Every game novel** — none existed before, not in any training data
- Different mechanics and reasoning types per game
- Every level builds on prior levels — no skipping

**Crucial catch: no instructions.**

> "The games don't come with instructions. So that means that this forces the test taker to explore its environment, to acquire goals on the fly, to build a world model, and to learn continuously."

> "This means that the agents that beat ARC-AGI-3 will show the first signs of continually updating their world model. You simply can't beat V3 otherwise."

**Human baselines** (crucial for scoring):
- Every game confirmed **human-solvable** (general public, no pre-screening, no special training)
- If a game was too hard for humans, it was excluded from the benchmark
- ARC counted **actions** humans took to complete each game — establishing an efficiency baseline
- "Since humans are our only proof point of general intelligence, we now have a baseline for how quickly general intelligence can solve these games."

## Current AI failure modes on ARC-AGI-3

Speaker names two specific failure modes observed in frontier models:

1. **Poor forward simulation** — "AI has a very difficult time anticipating future events. When it needs to run a simulation in its head, when it needs to understand how its actions right now will impact the world five or six moves ahead, it's unable to do that."

2. **Inability to learn from experience within a session** — "AI is currently unable to learn from its previous experiences to inform what it should be doing next. So it may latch on to an early hypothesis and be unable to deviate away. Or one of the more colorful examples is it thinks it's playing a different game. It plays one of these games and it has such strong anchoring within its training set that it thinks it's playing [a known game] and it's unable to realize that it's not actually that game."

**Summary**: "Today's best agents still need humans in the loop, but the agents that beat V3 will show that they do not require that level of supervision."

## Current frontier AI score on ARC-AGI-3

> **"Out of the gate, like I said, every game is solvable by humans and tier AI currently scores under 1%. This is the only unsaturated agent benchmark that we know."**

## Scoring — algorithmic learning efficiency

Not accuracy. Not "did you beat the level." Instead:

> "Because we have human baselines, we're able to compare how many actions AI took directly to how many actions humans took in order to do the same. And we will score based off this efficiency. Which means that if you score 100% on ARC-AGI-3, that means that you didn't just beat every game, but you did it matching or surpassing human-level efficiency."

> "For everybody who might think about just trying to brute force these games, it'll be poor efficiency... This measure of learning efficiency — this is really algorithmic learning efficiency. This is something that no other benchmark has right now."

## The four abilities ARC-AGI-3 isolates

To beat ARC-AGI-3, an agent must:
1. **Explore** an unknown environment
2. **Acquire its own goals** (no instructions given)
3. **Build a world model on the fly**
4. **Learn continuously**

> "These are some of the same capabilities that we see missing from current AI benchmarks or current coding agents today."

## ARC Prize 2026 ($2M competition)

- **Two tracks**:
  1. ARC-AGI-3 main competition (tested against hidden holdout set, partnered with Kaggle, Kaggle upgraded their platform to support the engine)
  2. **Last year of ARC-AGI-2** with **guaranteed grand prize** (someone will win it)
- 25 public games available for people to play immediately
- arcprize.org has agent-building resources

## Closing — fireside with Chollet and Altman

The speaker closed by announcing a fireside conversation between **Francois Chollet** (ARC Prize creator) and **Sam Altman** (OpenAI CEO), moderated by **DD Doss** of Menlo Ventures.

The fact that Altman is at an ARC Prize launch event validates the framework's legitimacy at the frontier-lab CEO level.

---

## Why this is in the Council materials folder

Partner sent this with "I have another video that the council will find quite interesting." Council voices are asked to read and produce takes with attention to:

- **Overlap with Ganuda's SkillRL epic** (self-improving skill library, experience bank augmentation, already council-approved #fb526dd2212e09a7)
- **Overlap with Patent #4 Graduated Autonomy Tiers** (especially the proposed "self-modification within bounded inference" broadening already in the Hulsey prep)
- **Overlap with federation thesis on L6 governance + world-model building**
- **Whether Ganuda should enter the ARC Prize 2026 competition**
- **How ARC-AGI-3's falsifiable framing ("we'll know when we can't find problems humans can do and AI can't") relates to Ganuda's own governance framing**

Filed alongside `BRIDLE-LE-RANDOM-APR11-2026.md` and `CARLINI-ANTHROPIC-SECURITY-APR11-2026.md`.
