# ARC-AGI-3 Agent Harness — Ganuda Federation

Bilateral Coordinated Tribal Intelligence playing ARC-AGI-3 via Playwright.

## Architecture

```
Canvas pixel reading (JavaScript)     → structured game state (grid, player, fuel, blocks, +)
    ↓
Thermal memory query (bluefin)        → "have I seen this pattern before?"
    ↓
Specialist Council vote (bmasass)     → "what move, and why?" (multi-voice deliberation)
    ↓
Graduated Autonomy Tier gate          → commit readiness (reflex / deliberation / council)
    ↓
Playwright keyboard press (redfin)    → execute move
    ↓
Thermal memory write                  → save experience for next level/game
```

## Components

- `agent.py` — main agent loop
- `perception.py` — canvas pixel reading via Playwright JavaScript injection
- `deliberation.py` — specialist_council.py integration for move decisions
- `memory.py` — thermal memory Experience Bank for cross-level learning
- `game.py` — Playwright browser session management + game interaction

## Evidence base for the architecture (Sam Walton store walk, Apr 12 2026)

1. **STEVE-EYE** (BAAI 2023) — validates perception/knowledge/planning decomposition
2. **MoE Routing Distraction** (Yonsei/Alibaba Apr 2026) — proves monolithic routing fails
3. **Be My Eyes** (Nov 2025) — Qwen2.5-VL-7B perceiver + LLM reasoner beats GPT-4o
4. **Ganuda** — extends perceiver/reasoner pair → governed multi-specialist council

## Contest entry

- CDR: `/ganuda/docs/council/CDR-CONTEST-ENTRY-APR12-2026.md`
- Patent gate: Hulsey Monday Apr 13 10:30 CT must clear IP exposure before submission
- Allocation: 55% contest-thesis / 30% new projects / 15% maintenance
