# JR INSTRUCTION: Document DC-6 Gradient Principle in Governance Docs

**Task ID**: DC6-GOV-001
**Kanban**: #1944
**Priority**: 2

## Objective

Create a governance design document for DC-6 (Gradient Principle). This is the ratified design constraint: "Specialization is gravity, not boundary. Cherokee scaffolding, not Roman walls. Everyone can speak to anything; they REST in different places."

## File

Create `/ganuda/docs/design/DC-6-GRADIENT-PRINCIPLE-MAR04-2026.md`

```text
# DC-6: Gradient Principle — Design Constraint Document

**Ratified**: March 4, 2026
**Longhouse Session**: 17a2bcc343c50619 (DC-7 session, DC-6 ratified alongside)
**Status**: ACTIVE — All council and enzyme operations must respect this constraint

---

## Statement

Specialization is gravity, not boundary. Cherokee scaffolding, not Roman walls.
Everyone can speak to anything; they REST in different places.

## What This Means

1. **No hard role boundaries**: Crawdad CAN comment on market strategy. Deer CAN flag a security concern. The Council is not a set of silos — it is a gradient field where each seat has a center of gravity.

2. **Gravity, not walls**: Each specialist has a domain where their opinion carries the most weight. Crawdad's gravity is security. Raven's gravity is strategy. Turtle's gravity is long-term impact. But gravity falls off smoothly — it doesn't hit a wall.

3. **Cherokee scaffolding**: The framework supports growth in any direction. Roman walls define what's inside and outside. Scaffolding lets you build wherever you need to, then move the scaffolding.

4. **REST positions**: Each specialist rests in their domain by default. When activated (substrate arrives), they respond from their gravity center. But they are free to move toward other domains when the signal warrants it.

## Implementation

### Epigenetic Modifiers (DEPLOYED)
DC-6 is implemented as an epigenetic modifier (`dc6_gradient`) in the `epigenetic_modifiers` table:
- Injects gradient-awareness context into each enzyme's system prompt
- Tells each enzyme where its gravity is and how to weight signals by proximity
- Active modifiers: `coyote_cam` (gravity: observation), `crawdad_scan` (gravity: security)

### Council Guidance Maps (DEPLOYED)
Each specialist has a guidance file in `/ganuda/config/council_guidance/`:
- crawdad.md, turtle.md, raven.md, gecko.md, eagle_eye.md, spider.md, peace_chief.md, coyote.md
- Each file defines the specialist's gravity center and gradient behavior

### Enzyme Context Profiles (DEPLOYED)
YAML profiles in `/ganuda/lib/duplo/context_profiles/` define each enzyme's default behavior.
The gradient is enforced through the system prompt: "Your gravity is X. You CAN reference any domain but you REST in Y."

## Anti-Patterns

- DO NOT reject a specialist's input because "that's not their domain"
- DO NOT weight all specialists equally on all topics (that's no gradient — that's flat)
- DO NOT create new specialists for every new domain (gradient means existing specialists stretch toward it)

## Relationship to Other Design Constraints

- **DC-1 (Lazy Awareness)**: Gradient saves energy — specialists don't burn ATP on topics far from their gravity
- **DC-5 (Coyote as Cam)**: Coyote Cam's gravity is observation — it doesn't act, just signals
- **DC-7 (Noyawisgi)**: Under pressure, the gradient field can shift — a specialist may temporarily move closer to an unfamiliar domain if survival requires it

## Cultural Root

The Cherokee clan system is a gradient, not a boundary. A member of the Wolf Clan has responsibilities centered on war and protection, but can participate in ceremonies, governance, or healing. The clan defines where you REST, not what you're allowed to do. DC-6 applies this principle to AI architecture.
```

## Verification

File exists at the specified path and contains all sections.
