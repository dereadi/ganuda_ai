# JR Instruction: Darrell's AI-Powered Portfolio Site

## Metadata
```yaml
task_id: darrell_ai_portfolio
priority: 1
assigned_to: VetAssist Jr. (reuse frontend patterns)
target: new site
estimated_effort: medium (1-2 days)
inspiration: https://sample-ai-resume.lovable.app/
reference_video: Nate B. Jones - "LinkedIn is dead" (Jan 2026)
```

## Strategic Context

Traditional job hunting has a **0.4% success rate**. Instead of optimizing for broken ATS filters, we build an AI interface that:

1. **Demonstrates depth** through conversation, not bullet points
2. **Inverts the power dynamic** with a fit assessment tool
3. **Shows self-awareness** by publishing strengths AND gaps
4. **Proves capability** by being the thing itself (built AI infrastructure)

> "The same AI that broke hiring enables a different move. Instead of squeezing through their filters, you create the surface where people encounter you on your own terms."

## Darrell's Unique Advantages

| Asset | How It Differentiates |
|-------|----------------------|
| **Cherokee AI Federation** | Built a 6-node AI inference cluster from scratch |
| **VetAssist** | Live production app helping veterans |
| **Thermal Memory** | 5,200+ documented experiences to query |
| **LLM Gateway** | Production API with 7-specialist Council |
| **TPM Experience** | Managing AI agents, roadmaps, infrastructure |
| **CVMA Membership** | Veteran community connection |
| **Non-linear Path** | IT → Linux → AI/ML → TPM |

## Site Structure

### Domain Options
- darrellreadi.com
- darrell.cherokee.ai
- readi.dev

### Pages

```
/
├── Hero Section
│   ├── Name: Darrell Readi
│   ├── Title: "Technical Program Manager | AI Infrastructure"
│   ├── Tagline: "I build AI systems that serve communities"
│   └── [Ask AI About Me] button (prominent)
│
├── Experience Section (expandable AI context)
│   │
│   ├── Cherokee AI Federation (2024-Present)
│   │   ├── Bullet: "Built 6-node AI inference federation"
│   │   └── [View AI Context] → Full story:
│   │       - Situation: Needed self-hosted LLM infrastructure
│   │       - Task: Design multi-node cluster with Council validation
│   │       - Action: Deployed vLLM, built LLM Gateway, created Jr agents
│   │       - Result: Production system serving VetAssist
│   │       - Lesson: Small teams can build enterprise-grade AI
│   │
│   ├── VetAssist Platform (2025-2026)
│   │   ├── Bullet: "Launched AI-powered VA claims assistant"
│   │   └── [View AI Context] → Full story:
│   │       - Free for veterans, sustainable via VSO subscriptions
│   │       - Calculator, chat, claim workbench
│   │       - PII isolation architecture (goldfin vault)
│   │       - CVMA pilot partnership
│   │
│   ├── Previous IT/Linux Roles
│   │   └── [View AI Context] → Infrastructure depth
│   │
│   └── Military Service / CVMA
│       └── Combat veteran perspective
│
├── Skills Matrix (3 columns)
│   │
│   ├── STRONG
│   │   ├── AI/LLM Infrastructure (vLLM, Ollama, quantization)
│   │   ├── Linux Systems Administration
│   │   ├── PostgreSQL / Database Design
│   │   ├── Python (FastAPI, async)
│   │   ├── Network Architecture (VLANs, Tailscale)
│   │   ├── Technical Program Management
│   │   └── AI Agent Orchestration
│   │
│   ├── MODERATE
│   │   ├── Frontend (Next.js, React)
│   │   ├── Cloud (AWS, moving to self-hosted)
│   │   ├── Kubernetes / Containers
│   │   └── Security / PKI
│   │
│   └── GAPS (honest)
│       ├── Mobile Development
│       ├── Consumer Product at Scale
│       └── Enterprise Sales / BD
│
├── Live Projects
│   ├── VetAssist → https://vetassist.cherokee.ai (live link)
│   ├── LLM Gateway → API docs, architecture diagram
│   ├── 7-Specialist Council → Explain the innovation
│   └── Cherokee AI Federation → Network diagram
│
├── AI Chat Interface
│   ├── "Ask me anything about my experience"
│   ├── Trained on thermal memory
│   ├── Can discuss any project in depth
│   ├── Handles multi-turn conversations
│   └── Acknowledges gaps honestly
│
└── Fit Assessment Tool
    ├── "Paste a job description"
    ├── AI analyzes against experience
    ├── Returns: STRONG FIT / MODERATE FIT / NOT A FIT
    ├── With reasoning and evidence
    └── Honest about gaps
```

## AI Context Documents

### 1. Career Summary Context

```markdown
# Darrell Readi - Career Context

## Current Role
Technical Program Manager for Cherokee AI Federation, a self-funded AI infrastructure project building ethical, community-serving AI systems.

## Core Philosophy
"For the Seven Generations" - Building technology that serves communities long-term, not just short-term profits.

## Key Projects

### Cherokee AI Federation (2024-Present)
Built a 6-node AI inference cluster from consumer hardware:
- redfin: GPU inference (RTX 5090, 96GB Blackwell)
- bluefin: PostgreSQL database
- greenfin: Monitoring and daemons
- goldfin: PII vault (VLAN isolated)
- silverfin: Identity management (FreeIPA)
- sasass/sasass2: Mac Studio edge nodes

Technical achievements:
- vLLM serving Qwen2.5-32B at 27 tok/sec
- LLM Gateway with OpenAI-compatible API
- 7-Specialist Council for response validation
- Thermal memory archive (5,200+ entries)
- Jr agent system for distributed task execution

### VetAssist Platform (2025-2026)
AI-powered assistant for U.S. veterans navigating VA disability claims:
- Free for individual veterans
- Revenue model: VSO/organization subscriptions
- Features: Calculator, AI chat, claim workbench, document storage
- Privacy: PII isolated on dedicated vault (goldfin)
- Pilot partner: CVMA (Combat Veterans Motorcycle Association)

## Technical Depth

Infrastructure:
- Designed VLAN segmentation for PII isolation
- Implemented Tailscale mesh networking
- Built systemd services for production reliability
- PostgreSQL schema design for multi-tenant apps

AI/ML:
- vLLM deployment and optimization
- Model quantization (AWQ, GGUF)
- Prompt engineering and system design
- RAG architecture design

Software:
- FastAPI backend development
- Next.js frontend development
- Python async programming
- Database design and optimization

## Management Style
- Write detailed JR instructions for AI agents
- Consult 7-specialist Council for decisions
- Track everything in thermal memory
- Phased roadmaps with clear milestones
- "TPM who doesn't write code directly"

## What I'm Looking For
Roles where I can:
- Build AI infrastructure that serves real communities
- Work with teams who value long-term thinking
- Apply TPM skills to emerging AI challenges
- Continue the "Assist" platform vision
```

### 2. Experience Deep Dives

Create expandable context for each experience entry with STAR format:
- **Situation**: What was the context/problem?
- **Task**: What was I responsible for?
- **Action**: What did I actually do?
- **Result**: What was the outcome?
- **Lesson**: What did I learn?

### 3. Fit Assessment Prompt

```markdown
# Fit Assessment System Prompt

You are an AI assistant helping evaluate job fit for Darrell Readi.

Given a job description, analyze it against Darrell's experience and provide an honest assessment.

## Darrell's Strengths
- AI/LLM infrastructure (built production systems)
- Linux systems administration
- Technical program management
- Database design (PostgreSQL)
- Network architecture
- AI agent orchestration

## Darrell's Moderate Areas
- Frontend development (can do it, not primary strength)
- Cloud platforms (AWS experience, prefers self-hosted)
- Kubernetes (understands concepts, not daily driver)

## Darrell's Gaps
- Mobile development (no experience)
- Consumer product at scale (B2B/internal tools background)
- Enterprise sales/BD (technical, not sales)

## Assessment Format

Analyze the job description and return:

### Fit Level: [STRONG FIT / MODERATE FIT / NOT A FIT]

### Why:
[2-3 sentences explaining the assessment]

### What Transfers:
- [Relevant experience point 1]
- [Relevant experience point 2]
- [Relevant experience point 3]

### Gaps to Consider:
- [Honest gap 1]
- [Honest gap 2]

### Recommendation:
[If STRONG FIT: "Let's talk. Here's my contact..."]
[If MODERATE FIT: "Could work with ramp-up time. Worth a conversation if..."]
[If NOT A FIT: "I'm probably not your person for this specific role, but if you have roles involving X, I'd be interested."]

Be honest. Darrell values authenticity over false positives.
```

## Technical Implementation

### Stack (Reuse VetAssist Patterns)

```
Frontend: Next.js 14 (same as VetAssist)
Styling: Tailwind CSS
AI Backend: LLM Gateway (/v1/chat/completions)
Context: Thermal memory queries
Hosting Options:
  - Vercel (free tier, public)
  - Redfin (self-hosted, on-brand)
Domain: TBD
```

### Key Components

```typescript
// AskAI button component
<AskAIButton
  context={careerContext}
  placeholder="Ask about my experience with AI infrastructure..."
/>

// Experience card with expandable context
<ExperienceCard
  title="Cherokee AI Federation"
  role="Technical Program Manager"
  period="2024-Present"
  bullets={["Built 6-node AI inference cluster"]}
  aiContext={cherokeeAIContext}
/>

// Skills matrix
<SkillsMatrix
  strong={["AI/LLM Infrastructure", "Linux", "PostgreSQL"]}
  moderate={["Frontend", "Cloud", "K8s"]}
  gaps={["Mobile", "Consumer Product", "Sales"]}
/>

// Fit assessment tool
<FitAssessment
  systemPrompt={fitAssessmentPrompt}
  experienceContext={fullCareerContext}
/>
```

### API Endpoints

```
POST /api/chat          - AI chat about experience
POST /api/fit-check     - Analyze job description
GET  /api/context/:key  - Get specific experience context
```

## Content to Extract from Thermal Memory

Query thermal memory for Darrell's key experiences:

```sql
SELECT content, context, timestamp
FROM thermal_memory_archive
WHERE memory_type IN ('achievement', 'project', 'decision')
  AND content ILIKE '%darrell%' OR content ILIKE '%tpm%'
ORDER BY resonance_score DESC
LIMIT 100;
```

Organize into:
1. Project narratives (STAR format)
2. Technical decisions and rationale
3. Leadership moments
4. Lessons learned

## Deployment Plan

### Phase 1: Basic Site (Day 1)
- [ ] Hero section with name/title
- [ ] Static experience section
- [ ] Skills matrix (3 columns)
- [ ] Live project links
- [ ] Basic styling

### Phase 2: AI Integration (Day 1-2)
- [ ] AI chat component
- [ ] Connect to LLM Gateway
- [ ] Load career context
- [ ] Test multi-turn conversations

### Phase 3: Fit Assessment (Day 2)
- [ ] Job description input
- [ ] Fit analysis prompt
- [ ] Strong/moderate/weak response
- [ ] Honest gap acknowledgment

### Phase 4: Polish (Day 2)
- [ ] Mobile responsive
- [ ] SEO meta tags
- [ ] Analytics (optional)
- [ ] Deploy to Vercel or redfin

## Success Metrics

| Metric | Target |
|--------|--------|
| Site live | Within 2 days |
| AI chat working | Multi-turn conversations |
| Fit tool working | Honest assessments |
| First recruiter interaction | Within 2 weeks |
| Interview from site | Within 4 weeks |

## The Power Move

When Darrell applies to jobs, the application includes:

> "For a deeper look at my experience, visit [darrell.site]. You can ask the AI anything about my background - it's trained on my actual projects, not just bullet points."

This:
1. Differentiates immediately
2. Demonstrates AI fluency (for AI roles)
3. Shows confidence ("interrogate my experience")
4. Proves the thing by being the thing

---

*Cherokee AI Federation - For the Seven Generations*
*"Let them discover what you designed them to find."*
