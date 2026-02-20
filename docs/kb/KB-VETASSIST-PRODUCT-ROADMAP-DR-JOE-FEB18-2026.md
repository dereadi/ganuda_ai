# KB: VetAssist Product Roadmap — Dr. Joe Collaboration Follow-up
**Date**: February 18, 2026
**Council Vote**: #0774f4580abd0cdb (PROCEED, 0.89 confidence, high_stakes)
**Context**: Dr. Joe asked about unfulfilled ideas from Dec 27 - Jan 1 collaboration sessions

## Background

Dr. Joe (BigMa) collaborated with the Cherokee AI Federation Dec 27 - Jan 1 while TPM was traveling (NOLA). During those sessions, Joe and the Council:
- Analyzed VetClaims.ai, voted 7-0 UNANIMOUS to build competing platform
- Built VetAssist MVP in one day (calculator, Council chat, auth, educational resources, bluefin deployment)
- Created Tsalagi Yohvwi brand (Cherokee Vision) — adopted UNANIMOUSLY
- Upgraded Council architecture (MAR + SMADRL + MAGRPO)
- Planned Goldfin Inner Sanctum (Beelink SER7 as FreeIPA + PII vault)
- Wrote comprehensive 13-Jr mission brief (882 lines) covering entire platform vision

## What Was Built (Dec 27)
- VA disability calculator with bilateral factor (JR14)
- AI chatbot with 7-specialist Council validation (JR15)
- JWT authentication system (JR16)
- Educational resources with 10-15 seeded articles (JR17)
- Bluefin staging deployment (JR18)
- VA condition database (later expanded to 800+)
- Legal options reference document
- Teaching Stories / Reflexion system

## What Remains Unbuilt (11 Items)

### PROJECT 0: Infrastructure Prerequisites (14 SP)
| Item | SP | Sprint | Notes |
|------|----|--------|-------|
| K. BigMac Bridge | 1 | RC-2026-02E | Dr. Joe API bridge, port 9001. Currently DOWN. |
| I. Voting-First Council Mode | 5 | RC-2026-02E | Fast-path: vote first, deliberate on splits only |
| J. Goldfin Inner Sanctum | 8 | RC-2026-02E | FreeIPA + PII vault. BLOCKS Projects 2 and 4. |

### PROJECT 1: Open-Source Trust Foundation (18 SP)
| Item | SP | Sprint | Notes |
|------|----|--------|-------|
| D. Open-Source Core | 5 | RC-2026-03A | MIT calculator + templates on GitHub |
| E. Educational Content Library | 13 | RC-2026-03A | 50 guides, 20 templates, 10-module course |

Legal safe harbor requires educational tool positioning before monetization.

### PROJECT 2: Monetization Engine (21 SP)
| Item | SP | Sprint | Notes |
|------|----|--------|-------|
| C. Stripe Subscription | 8 | RC-2026-03B | Free/$29mo/$1-5K org tiers |
| B. VSO White-Label | 13 | RC-2026-04A | Multi-tenant for DAV/VFW/CVMA |

Depends on: Goldfin PII vault + Project 1 content live.

### PROJECT 3: Growth & Distribution (18 SP)
| Item | SP | Sprint | Notes |
|------|----|--------|-------|
| A. Browser Extension (TurboVets) | 13 | RC-2026-03B | Chrome/Firefox Manifest V3 for VA.gov |
| F. Veteran Influencer Program | 5 | RC-2026-04A | Reddit + 50 affiliates |

### PROJECT 4: Advanced Features (18 SP)
| Item | SP | Sprint | Notes |
|------|----|--------|-------|
| G. A2UI Declarative UI | 5 | RC-2026-04B | JSON-driven UI rendering |
| H. Physician Network | 13 | RC-2026-04B | Nexus letters, HIPAA required |

## Dependency Chain
```
J (Goldfin) ──────┬──→ C (Stripe) ──→ B (White-Label)
                   └──→ H (Physician Network)
D + E (Content) ──→ F (Influencers)
D + E (Content) ──→ C (Stripe) [need free tier to demo]
A (Browser Ext) ── independent but most valuable after content exists
I (Vote-First) ── independent, force multiplier
K (Bridge) ──── independent, do immediately
G (A2UI) ──── independent, low priority
```

## Sprint Plan
| Sprint | Items | SP | Target Date |
|--------|-------|----|-------------|
| RC-2026-02E | K, I, start J | 14 | Feb 21 |
| RC-2026-03A | D, E, finish J | 26 | Mar 7 |
| RC-2026-03B | C, A | 21 | Mar 21 |
| RC-2026-04A | B, F | 18 | Apr 4 |
| RC-2026-04B | G, H | 18 | Apr 18 |

**Total: ~117 SP across 5 sprints (Feb-April 2026)**

## Financial Model
- Budget: $80K Year 1 (using Cherokee stack)
- Conservative: $174K ARR at 10K users (500 premium × $29/mo)
- With 3 VSOs: $354K ARR ($174K consumer + $9-15K B2B)
- Break-even: Month 8-9
- Kill criteria: <1K users at 6 months, any legal threat, CAC > LTV

## Key Decisions
1. Educational positioning FIRST (legal safe harbor)
2. Open-source core builds trust before monetization
3. Goldfin PII vault is the critical path blocker
4. Browser extension is the "killer feature" for stickiness
5. Physician network is last due to HIPAA complexity
6. Cherokee constitutional constraint: confidence <90% escalates to human

## Related
- Council Vote: #0774f4580abd0cdb
- Original ULTRATHINK: ULTRATHINK-VETCLAIMS-PLATFORM-DEC27-2025.md
- Legal Reference: VETCLAIMS_LEGAL_OPTIONS_REFERENCE_DEC2025.md
- Original Jr Brief: JR_VETCLAIMS_PLATFORM_BUILD_DEC27.md
- Prototype Build: JR_VETASSIST_PROTOTYPE_BUILD_DEC27.md

FOR SEVEN GENERATIONS
