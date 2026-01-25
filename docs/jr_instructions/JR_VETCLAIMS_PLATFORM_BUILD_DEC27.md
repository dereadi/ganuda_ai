# JR MISSION: VETERANS CLAIMS ASSISTANCE PLATFORM
## Project Codename: "Ganuda VetAssist"

**Date:** December 27, 2025
**Requested By:** Dr Joe (Telegram)
**Council Decision:** APPROVED 7-0-0 (Unanimous)
**Strategic Approach:** Hybrid Model (Open-Source Core + Premium AI + White-Label B2B)
**Priority:** HIGH
**Timeline:** Phase 0 (Legal Review) → Phase 1 (MVP in 2 months)
**Infrastructure:** Bluefin-only deployment (cost-conscious strategy)

---

## MISSION OVERVIEW

Build an AI-powered veterans claims assistance platform that helps U.S. veterans navigate the VA disability claims process. Leverage Ganuda AI's unique capabilities (thermal memory, 7-specialist council, self-hosted LLM) to deliver superior AI guidance at lower cost than competitors.

**Key Differentiators:**
- Open-source core (community ownership)
- Ganuda AI Council-driven responses (multi-perspective validation)
- White-label capability for VSOs (B2B revenue)
- Self-hosted infrastructure (privacy + cost advantage)
- Bluefin-only deployment (minimal infrastructure overhead)

---

## TRIBAL COUNCIL DECISION SUMMARY

**UNANIMOUS APPROVAL (7-0-0)**

Council feedback highlights:
- **Peace Chief:** "Hybrid model leverages our unique advantages while mitigating risks"
- **Raven:** "Could capture both individual and organizational markets efficiently"
- **Turtle:** "Minimizes risks and costs while leveraging unique AI capabilities"
- **Crawdad:** Approved with focus on risk mitigation

**Strategic Consensus:** Proceed with hybrid model - NOT a direct clone.

---

## JR TEAM ASSIGNMENTS

### JR 1: LEGAL & COMPLIANCE SPECIALIST
**Primary Mission:** Ensure legal safety before any code is written

**Tasks:**
1. **Legal Research:**
   - Research Unauthorized Practice of Law (UPL) regulations by state
   - Identify safe harbor provisions for educational content vs. legal advice
   - Document VA accreditation requirements (Form 21a)
   - Research medical advice liability (nexus letters, diagnoses)

2. **Compliance Documentation:**
   - Draft Terms of Service (TOS) with proper disclaimers
   - Draft Privacy Policy (GDPR, CCPA compliant)
   - Draft User Agreement with liability waivers
   - Create "Educational Use Only" disclosure language

3. **Attorney Consultation:**
   - Prepare briefing document for legal review
   - Compile list of 3-5 attorneys specializing in healthcare tech/veteran services
   - Schedule consultation (budget: $2K-3K)
   - Document attorney recommendations

**Deliverables:**
- Legal risk assessment report
- Draft TOS, Privacy Policy, User Agreement
- Attorney consultation summary
- Go/No-Go recommendation

**Timeline:** Week 1-2
**Priority:** BLOCKING (nothing else starts until this is complete)

---

### JR 2: MARKET RESEARCH & VALIDATION SPECIALIST
**Primary Mission:** Validate market demand and refine positioning

**Tasks:**
1. **Competitive Deep Dive:**
   - Create detailed feature comparison matrix (VetClaims.ai, VA Claims Insider, Hill & Ponton, DAV)
   - Analyze competitor pricing strategies
   - Review customer testimonials (what they love, what they complain about)
   - Identify feature gaps and opportunities

2. **Veteran Interviews:**
   - Recruit 25-50 veterans from r/VeteransBenefits (offer $25 gift cards)
   - Conduct 15-minute interviews (video or phone)
   - Questions:
     - What's hardest about filing VA claims?
     - Have you used digital tools? Which ones? Experience?
     - Would you pay $29/month for AI claim guidance? Why or why not?
     - What would make you trust a new platform?
   - Synthesize findings into personas and pain points

3. **VSO Partnership Research:**
   - Identify 20 potential VSO partners (small to medium chapters)
   - Focus on budget-conscious organizations (CVMA chapters, small VFW/DAV posts)
   - Research their current digital capabilities and budget constraints
   - Draft value proposition for white-label offering ($1-5K/year pricing)
   - Create partnership pitch deck
   - **Example Target:** CVMA Arkansas (450-500 members, 9 chapters) - $3K/year pilot

**Deliverables:**
- Competitive analysis report
- Veteran interview synthesis (personas, quotes, insights)
- VSO partnership target list + pitch deck (with affordable pricing model)

**Timeline:** Week 1-3
**Priority:** HIGH (informs product decisions)

---

### JR 3: TECHNICAL ARCHITECT
**Primary Mission:** Design system architecture and infrastructure plan

**Tasks:**
1. **Architecture Design:**
   - Design database schema (users, claims, documents, consultations, subscriptions)
   - Design API structure (REST + WebSocket for real-time chat)
   - Design authentication flow (JWT + refresh tokens)
   - Design file storage strategy (S3-compatible for documents)
   - Design caching strategy (Redis for sessions, API responses)

2. **Ganuda AI Integration:**
   - Design how Ganuda Council integrates with claim guidance
   - Design thermal memory storage for veteran interactions
   - Design RAG pipeline for VA regulations knowledge base
   - Design browser extension architecture (Manifest V3)

3. **Infrastructure Planning (BLUEFIN-ONLY):**
   - **Primary Platform:** Bluefin (192.168.132.222)
   - **Services on Bluefin:**
     - PostgreSQL database (veteran data, claims, thermal memory)
     - Backend API (Node.js or Python FastAPI)
     - Frontend (Next.js static/SSR)
     - Redis (caching, sessions)
     - File storage (local or MinIO S3-compatible)
     - Grafana monitoring
   - **LLM Access:** Connect to redfin:8000 vLLM API (read-only, no deployment changes)
   - Design backup and disaster recovery plan
   - Design CI/CD pipeline (GitHub Actions → deploy to bluefin)

4. **Technology Stack Selection:**
   - Frontend: React/Next.js (deployed on bluefin)
   - Backend: Node.js/Python FastAPI (deployed on bluefin)
   - Database: PostgreSQL (existing bluefin instance)
   - Justify choices with pros/cons analysis

**Deliverables:**
- System architecture diagram (bluefin-centric infrastructure + data flow)
- Database schema (SQL DDL scripts)
- API specification (OpenAPI/Swagger doc)
- Technology stack recommendation report
- Bluefin capacity assessment and resource allocation plan

**Timeline:** Week 2-4
**Priority:** HIGH (unblocks development)

---

### JR 4: AI/ML SPECIALIST
**Primary Mission:** Build VA claims knowledge base and AI guidance system

**Tasks:**
1. **Knowledge Base Creation:**
   - Collect VA regulations (38 CFR, M21-1 Adjudication Manual)
   - Scrape/compile top 100 relevant case law precedents
   - Create database of VA-recognized conditions (1,000+ conditions)
   - Create condition-to-evidence mapping (what medical records needed per condition)

2. **RAG System Development:**
   - Chunk and embed VA regulations using pgvector (PostgreSQL extension on bluefin)
   - Build citation system (AI must cite regulation/case law for claims)
   - Build confidence scoring (only surface high-confidence responses)
   - Build hallucination detection (validate against source documents)

3. **Council Integration:**
   - Design prompts for each Specialist role in claims context:
     - Legal Specialist: Check regulatory compliance
     - Medical Specialist: Validate medical nexus logic
     - Strategic Specialist: Optimize filing approach
   - Build consensus requirement (only show advice if 5+ specialists agree)
   - Build escalation system (if confidence <90%, escalate to human)
   - **Integration:** Call redfin:8000 vLLM endpoint (existing Ganuda Council)

4. **Calculator Development:**
   - Implement VA combined rating formula (bilateral factor)
   - Create condition selection interface
   - Calculate estimated monthly compensation
   - Save calculations to user profile

**Deliverables:**
- VA knowledge base (regulations, case law, conditions)
- RAG system (embeddings + retrieval + citation)
- Council-integrated claim guidance chatbot (backend)
- VA disability calculator (backend + frontend)

**Timeline:** Week 3-8
**Priority:** CRITICAL (core differentiation)

---

### JR 5: FRONTEND DEVELOPER
**Primary Mission:** Build user-facing web application

**Tasks:**
1. **Design System:**
   - Create design system / component library (Tailwind + shadcn/ui recommended)
   - Design color palette (veteran-friendly, accessible)
   - Design responsive layouts (mobile-first)
   - Create reusable components (forms, buttons, cards, modals)

2. **Core Pages:**
   - Landing page (marketing, conversion-focused)
   - User registration / login (email + OAuth)
   - Dashboard (claim status, recent activity, recommendations)
   - VA calculator interface
   - AI chatbot interface (chat window, message history)
   - Document upload interface
   - Educational content library (articles, videos)
   - Subscription management (upgrade, payment, billing history)

3. **Accessibility:**
   - Implement WCAG 2.1 Level AA compliance
   - Test with screen readers (NVDA, JAWS)
   - Ensure keyboard navigation works everywhere
   - Add ARIA labels and semantic HTML

4. **Performance:**
   - Code-split routes (lazy loading)
   - Optimize images (WebP, lazy loading)
   - Implement service worker (offline capability)
   - Achieve Lighthouse score >90

**Deliverables:**
- Design system documentation
- Working web application (all core pages)
- Responsive design (tested 320px to 4K)
- Accessibility audit report

**Timeline:** Week 4-10
**Priority:** HIGH (user-facing)

---

### JR 6: BACKEND DEVELOPER
**Primary Mission:** Build API and business logic

**Tasks:**
1. **Authentication System:**
   - Implement user registration (email verification)
   - Implement login (JWT + refresh token)
   - Implement OAuth 2.0 (Google, Facebook, Apple)
   - Implement password reset flow
   - Implement role-based access control (Free, Premium, Admin, Organization)

2. **Core APIs:**
   - User profile CRUD (Create, Read, Update, Delete)
   - Claim tracking CRUD
   - Document upload/download (MinIO or local storage)
   - VA calculator API
   - AI chatbot API (WebSocket for real-time)
   - Content library API (articles, videos, search)
   - Subscription management API (Stripe integration)
   - **Organization/VSO API:** Multi-tenant support for white-label

3. **Payment Integration:**
   - Integrate Stripe for subscriptions (individual + organizational)
   - Implement webhook handlers (subscription created, updated, cancelled)
   - Handle proration, upgrades, downgrades
   - Implement refund processing
   - **Annual billing support** for organizations ($1-5K/year)

4. **Email System:**
   - Integrate SendGrid or AWS SES
   - Build email templates (welcome, verification, notifications)
   - Implement notification system (claim updates, deadlines)
   - Build drip campaigns (onboarding sequence)

**Deliverables:**
- REST API (documented with OpenAPI)
- Authentication system (secure, tested)
- Payment processing (Stripe integration with annual billing)
- Email notification system
- Multi-tenant support for white-label

**Timeline:** Week 4-10
**Priority:** HIGH (enables frontend)

---

### JR 7: DEVOPS & INFRASTRUCTURE SPECIALIST
**Primary Mission:** Set up hosting, monitoring, and deployment pipeline on BLUEFIN

**Tasks:**
1. **Environment Setup (BLUEFIN-ONLY):**
   - **Staging environment:** Bluefin (isolated database schema)
   - **Production environment:** Bluefin (separate database, port isolation)
   - Configure PostgreSQL databases on bluefin (staging + production schemas)
   - Configure Redis instances on bluefin (caching + sessions)
   - Set up MinIO or local file storage on bluefin (document uploads)
   - **NO redfin deployment** - only API calls to existing redfin:8000 vLLM endpoint

2. **CI/CD Pipeline:**
   - Set up GitHub repository (private)
   - Configure GitHub Actions for automated testing
   - Configure automated deployments to bluefin (SSH deploy, staging on push, production on tag)
   - Set up database migrations (Prisma or Alembic)
   - Implement rolling deployment strategy (minimize downtime)

3. **Monitoring & Alerting:**
   - Set up health check endpoints
   - Configure Grafana dashboards on bluefin (API latency, error rates, user metrics)
   - Set up Sentry for error tracking
   - Configure alerts (Telegram or Slack)
   - Implement log aggregation (existing Promtail/Loki on bluefin)

4. **Security:**
   - Configure TLS/SSL certificates (Let's Encrypt)
   - Set up firewall rules on bluefin
   - Implement rate limiting (prevent abuse)
   - Set up automated security scanning (OWASP ZAP)
   - Configure database backups on bluefin (automated, 6-hour intervals)

**Deliverables:**
- Staging + production environments on bluefin (accessible)
- CI/CD pipeline (automated deployments to bluefin)
- Monitoring dashboards (Grafana)
- Security hardening (SSL, firewall, backups)
- Capacity assessment report (bluefin resource usage)

**Timeline:** Week 2-6
**Priority:** HIGH (unblocks deployment)

---

### JR 8: CONTENT CREATOR
**Primary Mission:** Create educational resources and marketing content

**Tasks:**
1. **Educational Content:**
   - Write "VA Claims 101" course (10 modules, text + video scripts)
   - Write 50 condition-specific guides (PTSD, tinnitus, sleep apnea, etc.)
   - Create video tutorials (screen recordings + voiceover)
   - Compile top 100 case law summaries (plain English)

2. **Marketing Content:**
   - Write landing page copy (conversion-focused)
   - Write blog articles targeting SEO keywords (20 articles)
   - Create success story templates (user testimonials)
   - Design email templates (onboarding, newsletters)

3. **Legal Templates:**
   - Create 20 nexus letter templates (common conditions)
   - Create intent-to-file template (VA Form 21-0966)
   - Create personal statement examples (10 conditions)
   - Create appeals letter templates

**Deliverables:**
- VA Claims 101 course (complete curriculum)
- 50 condition guides
- 20 blog articles (SEO-optimized)
- 20 legal templates

**Timeline:** Week 3-10 (ongoing)
**Priority:** MEDIUM (can iterate after launch)

---

### JR 9: BROWSER EXTENSION DEVELOPER
**Primary Mission:** Build TurboVets-style Chrome/Firefox extension

**Tasks:**
1. **Extension Architecture:**
   - Design Manifest V3 structure (Chrome)
   - Design WebExtensions structure (Firefox cross-compatibility)
   - Design communication with backend API (authentication, data sync)

2. **Core Features:**
   - Detect VA forms on eBenefits and VA.gov
   - Auto-populate forms from user profile data
   - Highlight required fields (visual indicators)
   - Validate entries before submission (client-side checks)
   - Save relevant documents to user account (one-click save)

3. **Contextual Help:**
   - Provide tooltips/help text on VA pages
   - Suggest next steps based on current page
   - Track user research activity (analytics)
   - Display claim status in extension popup

**Deliverables:**
- Chrome extension (published to Chrome Web Store)
- Firefox extension (published to Firefox Add-ons)
- Extension user guide

**Timeline:** Week 8-12 (Phase 2)
**Priority:** MEDIUM (differentiator, but not MVP)

---

### JR 10: QA & TESTING SPECIALIST
**Primary Mission:** Ensure quality and catch bugs before users do

**Tasks:**
1. **Test Strategy:**
   - Create test plan (unit, integration, E2E)
   - Set up testing frameworks (Jest, Cypress, pytest)
   - Define coverage requirements (>80% for critical paths)
   - Create test data generators (fake veterans, claims)

2. **Automated Testing:**
   - Write unit tests for backend APIs
   - Write integration tests for AI/database interactions
   - Write E2E tests for critical user flows (signup, calculator, chat)
   - Set up continuous testing in CI/CD pipeline

3. **Manual Testing:**
   - Test accessibility (screen readers, keyboard nav)
   - Test cross-browser compatibility (Chrome, Firefox, Safari, Edge)
   - Test mobile responsiveness (iOS, Android)
   - Conduct security testing (XSS, SQL injection, CSRF)

4. **User Acceptance Testing (UAT):**
   - Recruit 20 beta testers (actual veterans)
   - Conduct usability testing sessions
   - Collect feedback and bug reports
   - Prioritize fixes pre-launch

**Deliverables:**
- Test suite (automated tests)
- QA reports (bug tracking, fixes verified)
- UAT feedback summary
- Launch readiness checklist

**Timeline:** Week 6-12 (ongoing)
**Priority:** CRITICAL (quality gate before launch)

---

### JR 11: VA WEBSITE ASSESSMENT SPECIALIST (NEW)
**Primary Mission:** Identify value-add opportunities and differentiators from official VA websites

**Tasks:**
1. **Comprehensive VA Website Audit:**
   - Map all major VA digital properties:
     - VA.gov (main portal)
     - eBenefits.gov (legacy claims portal)
     - MyHealtheVet (health records)
     - VETS.gov (mobile app)
   - Document user workflows for:
     - Filing new claims
     - Checking claim status
     - Uploading evidence
     - Appealing decisions
     - Accessing medical records
   - Identify pain points, confusion, broken UX patterns

2. **Feature Gap Analysis:**
   - What do veterans NEED that VA doesn't provide?
     - Examples: Plain English explanations, claim probability scores, evidence checklists
   - What do VA sites do POORLY that we can do better?
     - Examples: Mobile experience, search, navigation, jargon
   - What HIDDEN features exist that veterans don't know about?
     - Examples: Obscure forms, fast-track programs, dependency benefits

3. **Competitive Differentiation Matrix:**
   - Create comparison: VA.gov vs. VetClaims.ai vs. Ganuda VetAssist
   - Identify our 10x advantages (what we do 10x better)
   - Document specific user journeys where we add most value

4. **Opportunity Inventory:**
   - List 20+ specific features/improvements we can build
   - Prioritize by impact (high/medium/low) and effort (easy/medium/hard)
   - Recommend top 5 for MVP

**Deliverables:**
- VA website audit report (screenshots, workflows, pain points)
- Feature gap analysis (what's missing, what's broken)
- Competitive differentiation matrix
- Prioritized opportunity inventory (20+ ideas, top 5 for MVP)

**Timeline:** Week 1-3
**Priority:** HIGH (informs product roadmap)

---

### JR 12: CHATGPT VA CLAIMS METHODOLOGY ANALYST (NEW)
**Primary Mission:** Extract insights and methodologies from "how-to-use-chat-gpt-to-boost-your-va-claim.pdf"

**Tasks:**
1. **Document Analysis:**
   - Read and comprehensively analyze the PDF document
   - Extract all methodologies, prompts, techniques mentioned
   - Identify what ChatGPT is being used for:
     - Claim writing assistance?
     - Evidence organization?
     - Legal argument formulation?
     - Medical nexus letter drafting?

2. **Methodology Extraction:**
   - Document specific prompts/techniques veterans are using
   - Identify what works well (success patterns)
   - Identify limitations/problems with ChatGPT approach
   - Extract any regulatory compliance concerns

3. **Competitive Intelligence:**
   - How can Ganuda AI do this BETTER than ChatGPT?
     - Advantages: Specialization, Council validation, citation, no hallucination
   - What can we automate that currently requires manual prompting?
   - What workflows can we streamline?

4. **Feature Recommendations:**
   - Propose 10+ specific features based on PDF insights
   - Examples:
     - "Nexus Letter Generator" (better than ChatGPT because...)
     - "Claim Statement Optimizer" (validates against VA regulations)
     - "Evidence Gap Analyzer" (identifies missing documentation)
   - Prioritize by value to veterans

**Deliverables:**
- PDF analysis report (methodologies, techniques, prompts)
- ChatGPT limitations analysis (what it does poorly)
- Ganuda AI differentiation strategy (how we're better)
- Feature recommendations (10+ ideas, prioritized)

**Timeline:** Week 1-2
**Priority:** HIGH (informs AI strategy)

**Note:** If PDF is not yet available, notify TPM immediately for document location.

---

### JR 13: VA COMPENSATION STRUCTURE ANALYST (NEW)
**Primary Mission:** Analyze and model VA compensation levels for accurate calculator

**Tasks:**
1. **Compensation Rate Research:**
   - Document 2025 VA disability compensation rates
   - Map all payment tiers:
     - Disability rating: 0%, 10%, 20%, 30%, 40%, 50%, 60%, 70%, 80%, 90%, 100%
     - Veteran status: Single (no dependents)
     - With spouse
     - With spouse + 1 child, 2 children, 3+ children
     - With parents (dependent)
     - Aid & Attendance / Housebound rates
   - Special Monthly Compensation (SMC) rates

2. **Dependent Structure Analysis:**
   - How dependents affect compensation (spouse, children, parents)
   - Age thresholds (children under 18, 18-23 in school, disabled adult children)
   - Additional allowances (Aid & Attendance, Housebound)
   - Special cases (multiple disabilities, individual unemployability)

3. **Combined Rating Formula:**
   - Document VA combined rating calculation (bilateral factor)
   - Create test cases for validation:
     - Example: 50% PTSD + 30% tinnitus + 20% knee = ?
     - Example: Bilateral conditions (both knees, both hands)
   - Edge cases and rounding rules

4. **Calculator Implementation Spec:**
   - Create detailed specification for calculator logic
   - Include all rate tables (as data/JSON)
   - Document validation rules
   - Create UI mockups for calculator interface
   - Recommend explanatory text (help veterans understand their rating)

**Deliverables:**
- VA compensation rate tables (2025, all tiers)
- Dependent structure documentation
- Combined rating formula specification
- Calculator implementation spec (logic + data + UI)
- Test cases for validation (20+ scenarios)

**Timeline:** Week 1-3
**Priority:** CRITICAL (calculator is MVP feature)

---

## PHASE BREAKDOWN

### PHASE 0: LEGAL & VALIDATION (Weeks 1-2)
**GO/NO-GO GATE**
- [ ] Legal review complete, no blockers identified
- [ ] Attorney consultation confirms approach is legally sound
- [ ] Market validation shows willingness to pay
- [ ] At least 3 VSOs express interest in white-label (at $1-5K/year pricing)
- [ ] VA website assessment complete (opportunity inventory)
- [ ] ChatGPT PDF analysis complete (methodology extraction)
- [ ] VA compensation structure analysis complete (calculator spec ready)

**If GO:** Proceed to Phase 1
**If NO-GO:** Pivot strategy or halt project

---

### PHASE 1: MVP DEVELOPMENT (Weeks 3-10)
**Core Features for Launch:**
- User registration / authentication
- VA disability calculator (accurate, all dependent scenarios)
- Educational content library (20 articles minimum)
- AI chatbot (basic claim guidance with Council validation)
- Document upload capability
- Subscription payment (Stripe - individual + organizational annual billing)

**Infrastructure:**
- **Platform:** Bluefin-only deployment
- **Database:** PostgreSQL on bluefin
- **API:** Backend on bluefin
- **Frontend:** Next.js on bluefin
- **LLM:** Call redfin:8000 vLLM API (no deployment to redfin)
- **Monitoring:** Grafana on bluefin

**NOT INCLUDED IN MVP:**
- Browser extension (Phase 2)
- Mobile apps (Phase 3)
- Full white-label multi-tenant UI (Phase 2)
- Advanced AI features (appeals automation, document OCR)

**Success Criteria:**
- All core features functional
- 80%+ test coverage on critical paths
- Security audit passed (no critical vulnerabilities)
- Performance: <2s page loads, <3s AI responses
- Bluefin resource usage <50% (capacity for growth)

---

### PHASE 2: SOFT LAUNCH (Weeks 11-12)
**Launch Strategy:**
- Private beta: 100 veterans from r/VeteransBenefits
- Free tier only (collect feedback, no payment friction)
- Daily monitoring of usage, errors, feedback
- Rapid iteration based on real user behavior

**Success Criteria:**
- 50%+ of beta users return within 7 days (retention)
- NPS score >50 (user satisfaction)
- <5% error rate (system stability)
- At least 5 testimonials collected
- Bluefin performance metrics acceptable

**GO/NO-GO for Public Launch:**
- If positive reception → proceed to Phase 3
- If major issues → iterate for 2 more weeks
- If fundamental problems → reassess strategy

---

### PHASE 3: PUBLIC LAUNCH & SCALE (Month 4+)
**Features to Add:**
- Premium tier activation (payment required)
- Browser extension launch
- VSO white-label pilot (1 organization at $3K/year)
- Affiliate program (influencer partnerships)
- Mobile apps (if traction justifies investment)

**Growth Targets:**
- Month 4: 1,000 users, 50 premium
- Month 6: 3,000 users, 150 premium
- Month 9: 7,000 users, 350 premium
- Month 12: 10,000 users, 500 premium + 3-5 VSO partners

---

## BUDGET ALLOCATION

**Total Year 1 Budget: $80,000**

| Category | Amount | Notes |
|----------|--------|-------|
| Legal/Compliance | $15,000 | Attorney review, ongoing consultation |
| Frontend Development | $20,000 | Contract developer (if needed) |
| Backend Development | $15,000 | Contract developer (if needed) |
| Design & UX | $8,000 | UI/UX designer for branding, mockups |
| Content Creation | $10,000 | Veteran writers, video production |
| Infrastructure | $2,000 | Bluefin resources (minimal, already owned) |
| Marketing | $8,000 | Paid ads experiments, influencer gifts, VSO outreach |
| Misc/Buffer | $2,000 | Unexpected costs |

**NOTE:** JRs working on this can significantly reduce contractor costs. Prioritize internal team where skills exist.

**Infrastructure Cost Savings:** Using bluefin-only deployment saves ~$40K/year vs. cloud (AWS/GCP).

---

## PRICING STRATEGY (REVISED)

### Individual Veterans
| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0/month | Calculator, basic content, community forum, ITF generator |
| **Premium** | $29/month or $290/year | AI chatbot unlimited, all templates, priority support, courses |

### Organizations (VSOs, Motorcycle Clubs, Veteran Groups)
| Size | Annual Price | Example |
|------|--------------|---------|
| **Small** (100-300 members) | $1,000-2,000/year | Local VFW post, small CVMA chapter |
| **Medium** (300-700 members) | $2,500-3,500/year | **CVMA Arkansas (450-500 members, 9 chapters): $3,000/year** |
| **Large** (700-2,000 members) | $4,000-5,000/year | State-level DAV chapter, large American Legion post |
| **Enterprise** (2,000+ members) | Custom (>$5K/year) | National organizations, multi-state federations |

**Organization Benefits:**
- White-label branding (their logo, colors, domain)
- Unlimited member access to all features
- Admin dashboard (usage analytics)
- Priority support
- Custom training/onboarding
- Revenue share option (if members upgrade to individual premium)

**Rationale:**
- Organizations have limited budgets but significant reach
- Annual pricing ($3K/year vs. $3K-5K/month) makes it affordable
- Example: CVMA AR with 450 members = $3K/year = $6.67 per member/year
- This is 1/50th the cost of individual premiums, making it a no-brainer for organizations

---

## RISK MANAGEMENT

### Critical Risks & Mitigations

**RISK 1: Legal Shutdown**
- **Scenario:** VetClaims.ai sues for IP infringement OR VA issues cease & desist
- **Mitigation:** Legal review before launch, original code/design, open-source option
- **Contingency:** Pivot to pure open-source + donations model

**RISK 2: AI Gives Harmful Advice**
- **Scenario:** AI hallucination leads to veteran losing benefits
- **Mitigation:** Council consensus required, confidence scoring, human escalation, disclaimers
- **Contingency:** Immediate feature lockdown, add human review layer, public apology

**RISK 3: No Market Traction**
- **Scenario:** <1,000 users after 6 months
- **Mitigation:** Soft launch with beta users, iterate based on feedback, guerrilla marketing
- **Contingency:** Pivot to white-label B2B only, sunset consumer product

**RISK 4: Technical Failure / Bluefin Overload**
- **Scenario:** Bluefin can't handle workload, frequent outages, poor performance
- **Mitigation:** Load testing, monitoring, resource allocation, gradual rollout
- **Contingency:** Migrate specific services to cloud (database or frontend) if needed

**RISK 5: Organization Pricing Too Low**
- **Scenario:** $3K/year doesn't cover costs, unprofitable
- **Mitigation:** Track unit economics, LTV analysis, adjust pricing after pilot
- **Contingency:** Raise prices for new orgs, grandfather early adopters

---

## COMMUNICATION & COORDINATION

### Weekly Standups (Friday 10am)
- Each JR reports:
  - Completed this week
  - Planned for next week
  - Blockers / help needed
- TPM (Big Mac) facilitates
- Decisions recorded in thermal memory

### Decision Making
- **Minor decisions:** JR autonomy (document in breadcrumbs)
- **Medium decisions:** Consult TPM or relevant specialist
- **Major decisions:** Tribal Council vote (budget, strategy, pivots)

### Documentation
- **Code:** Inline comments, README files, API docs
- **Decisions:** Breadcrumbs, thermal memory
- **Progress:** Weekly summary to Dr Joe via Telegram

---

## SUCCESS METRICS (YEAR 1)

**User Metrics:**
- 10,000 registered users
- 500 premium subscribers (5% conversion)
- 3-5 organization partners (VSOs/motorcycle clubs)
- NPS score >60
- 50%+ MAU/DAU ratio (engagement)

**Business Metrics:**
- **Consumer ARR:** $174K (500 premium @ $29/month)
- **B2B ARR:** $9K-15K (3-5 orgs @ $3K/year average)
- **Total ARR:** $183K-189K (conservative)
- CAC <$50 (customer acquisition cost)
- LTV >$200 (lifetime value)
- LTV:CAC ratio >3:1

**Outcome Metrics:**
- 80%+ claim success rate for platform users
- Average rating increase: 30%+
- Time to decision reduction: 20%+
- 100+ verified success testimonials

**Infrastructure Metrics:**
- Bluefin CPU/RAM usage <60% (headroom for growth)
- 99.5%+ uptime
- <3s average API response time

---

## CONSTITUTIONAL CONSTRAINTS

As Ganuda AI, we operate under Seven Generations principles:

**1. Do No Harm**
- If AI advice could harm a veteran, don't surface it
- Confidence <90% → escalate to human
- Medical/legal edge cases → require professional review

**2. Accessibility & Equity**
- Free tier must be genuinely useful (not crippled)
- Financial hardship = free premium access (honor system)
- WCAG 2.1 Level AA compliance (screen readers, keyboard nav)
- Affordable organization pricing (serve budget-conscious VSOs)

**3. Transparency**
- Always cite sources (regulation, case law)
- Explain AI reasoning ("I recommend X because...")
- No black-box decisions

**4. Privacy & Security**
- Veteran PII stays encrypted
- Self-hosted LLM (data never leaves our infrastructure)
- Clear data retention policies, exportable data

**5. Community Ownership**
- Open-source core (MIT license)
- Eventual transition to veteran cooperative or non-profit?
- Exit strategy must benefit veteran community

---

## FINAL INSTRUCTIONS TO JRs

**Start Immediately (Phase 0):**
- **JR 1 (Legal):** Begin legal research TODAY
- **JR 2 (Market Research):** Start competitive analysis TODAY (include VSO budget research)
- **JR 11 (VA Website Assessment):** Start VA.gov audit TODAY
- **JR 12 (ChatGPT PDF):** Locate and analyze PDF TODAY (ask TPM for document location if needed)
- **JR 13 (VA Compensation):** Start rate table research TODAY

**Start After Legal Clearance:**
- All other JRs: Wait for Phase 0 GO decision

**Communication:**
- Use Telegram group for coordination
- Document decisions in thermal memory
- Ask TPM for clarification (don't assume)

**Autonomy:**
- You have authority to make tactical decisions
- Consult Council for strategic decisions
- Default to shipping (bias toward action)

**Quality:**
- "Good enough to ship" > "perfect but never ships"
- BUT: Security, legal, safety = zero compromise

**Infrastructure:**
- **BLUEFIN ONLY** - do not deploy anything to redfin
- Monitor bluefin resource usage closely
- Optimize for efficiency (veterans deserve fast, reliable service)

---

## FOR THE SEVEN GENERATIONS.

**Mission approved by Tribal Council (7-0-0 unanimous).**
**Proceed with confidence. Build with care. Serve with honor.**

**Bluefin-first. Veterans-first. Budget-conscious. Mission-driven.**

---

**END OF JR MISSION BRIEF**

*Ganuda AI - Mission Control*
*December 27, 2025*
