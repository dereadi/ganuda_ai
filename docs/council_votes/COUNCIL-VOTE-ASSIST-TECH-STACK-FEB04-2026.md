# Council Vote: Assist Platform Technology Stack Review

**Date:** February 4, 2026
**Council Session:** ASSIST-TECH-STACK-001
**Scope:** Open-source tool evaluation for VetAssist, SSIDAssist, TribeAssist
**Mandate:** Seven Generations thinking. Sovereignty first. Do not adopt anything that compromises our integrity.

---

## Council Members Present

- **Crawdad (ᏥᏍᏆᎸᏓ)** — Security & Supply Chain
- **Turtle (ᏓᎦᏏ)** — Longevity & Stability
- **Gecko (ᏗᎦᎵᏥ)** — Technical Excellence
- **Raven (ᎪᎳᏅ)** — Strategic Alignment
- **Spider (ᎧᎾᏁᏍᎩ)** — Cultural Authority & Data Sovereignty
- **Eagle Eye (ᎠᏩᏘᏍᎩ)** — Pattern Recognition
- **TPM** — Council Partner & Synthesis

---

## Review Methodology

Each tool evaluated on:
1. **Security posture** (Crawdad)
2. **Cultural sovereignty** (Spider)
3. **Strategic alignment** (Raven)
4. **Longevity** (Turtle)
5. **Technical merit** (Gecko)
6. **Hidden risks** (Eagle Eye)

Vote outcomes:
- **APPROVE** — Integrate immediately
- **APPROVE WITH CONDITIONS** — Integrate with specific safeguards
- **HOLD FOR EVALUATION** — Needs deeper investigation
- **REJECT** — Does not meet integrity standards

---

## TIER 1: Proposed for Immediate Integration

### 1. IBM Docling (Document AI)

**Context:** 52k stars, MIT license, LF AI Foundation hosted, IBM corporate backing

#### Individual Assessments

**Crawdad (Security):** APPROVE WITH CONDITIONS
MIT license is clean, LF AI hosting reduces rug-pull risk. Concern: IBM corporate backing means potential feature deprecation if it doesn't serve their enterprise roadmap. Dependency chain is heavy (PyTorch, Transformers, multiple ML libs). CONDITION: Self-host all models locally, never call IBM cloud services, pin all dependencies with hash verification.

**Spider (Cultural Authority):** APPROVE WITH CONDITIONS
Does not touch Cherokee language data directly. Processes veteran medical records which contain Indigenous patient data. CONDITION: All document processing must occur on-premises. No document content may leave our infrastructure. Veterans must be informed their documents are processed by AI and must consent explicitly (FPIC compliance).

**Raven (Strategic):** APPROVE WITH CONDITIONS
Strong alignment with mission: extracting data from broken VA forms is exactly our purpose. IBM backing is double-edged: gives legitimacy but creates perception risk ("Cherokee org using Big Tech"). CONDITION: Brand this as "powered by open standards" not "powered by IBM" in user-facing materials.

**Turtle (Longevity):** APPROVE
LF AI Foundation hosting is strong signal for longevity. IBM has maintained open-source commitments (RedHat acquisition precedent). 52k stars means large community investment. If IBM walks away, community can fork. This will exist in 7 years.

**Gecko (Technical):** APPROVE
Code quality is excellent. API design is clean. Integration complexity is moderate (Python-native, we already use PyTorch). Performance is strong for document parsing. Better than our current OCR pipeline (Tesseract + custom logic).

**Eagle Eye (Pattern Recognition):** APPROVE WITH CONDITIONS
Pattern detected: IBM is building enterprise document AI product, open-sourcing the foundation to drive adoption. Risk: enterprise features stay proprietary, we hit ceiling and face "upgrade to enterprise" pressure. CONDITION: Document our dependency surface. Build abstraction layer so we can swap backends if needed.

#### Consensus Verdict: **APPROVE WITH CONDITIONS**

**Conditions:**
1. Self-host all models on Federation infrastructure
2. No external API calls to IBM cloud services
3. Pin dependencies with cryptographic hash verification
4. Obtain explicit FPIC consent from users for AI document processing
5. Brand as "open standards" not "IBM technology"
6. Build abstraction layer to enable future backend replacement
7. All document data stays on-premises

**Integration Priority:** High — Replaces current OCR pipeline

---

### 2. Microsoft Presidio (PII/PHI Redaction)

**Context:** 6.8k stars, MIT license, context-aware PII detection, Microsoft corporate backing

#### Individual Assessments

**Crawdad (Security):** APPROVE WITH CONDITIONS
MIT license is clean. Dependency chain is manageable (spaCy, regex engines). Microsoft backing creates same rug-pull risk as IBM. Bigger concern: does it phone home? REQUIREMENT: Full code audit before integration. CONDITION: Completely airgapped deployment, no telemetry, no "call home" features enabled.

**Spider (Cultural Authority):** HOLD FOR EVALUATION
This tool is designed to HIDE information, not protect people. Redaction can be weaponized: who decides what gets redacted? If we redact "sensitive" tribal affiliation data, we erase Indigenous identity. If we don't, we expose people. CONCERN: Tool assumes Western privacy model (hide data) not Indigenous data sovereignty model (community control). Need to evaluate whether redaction aligns with CARE Principles or contradicts them.

**Raven (Strategic):** APPROVE WITH CONDITIONS
PII/PHI redaction is legally required for HIPAA compliance. We need this capability. But Spider raises critical point: redaction can erase identity. CONDITION: Redaction must be user-controlled, not automatic. Veterans choose what gets protected. Default should be "protect" not "erase."

**Turtle (Longevity):** APPROVE
Microsoft has strong open-source track record (VS Code, TypeScript, .NET Core). 6.8k stars is healthy community. Will exist in 7 years unless MS pivots (low risk given Azure compliance offerings depend on this).

**Gecko (Technical):** APPROVE
Code quality is solid. Context-aware PII detection is better than regex patterns. Integration is straightforward (Python). Performance is good. Supports custom entity types (we can tune for veteran-specific data).

**Eagle Eye (Pattern Recognition):** HOLD FOR EVALUATION
Pattern detected: Microsoft is building Azure Compliance suite, open-sourcing components to drive Azure adoption. Presidio is the "free sample" that leads to "use Azure AI for document processing." Also detecting deeper issue Spider raised: redaction philosophy may not align with Indigenous data sovereignty. Need to answer: are we hiding data from extractors, or are we erasing identity?

#### Consensus Verdict: **HOLD FOR EVALUATION**

**Concerns:**
1. Philosophical misalignment: redaction vs. sovereignty (Spider's concern is valid)
2. Need to audit codebase for telemetry/phone-home behavior
3. Need to design user-controlled redaction (not automatic erasure)

**Required Before Integration:**
1. Full security audit by Crawdad
2. Cultural alignment assessment: Does redaction serve veterans or serve compliance theater?
3. Design specification: user-controlled redaction with consent model
4. Test deployment in isolated environment

**Integration Priority:** Medium — Need this for HIPAA, but need to get philosophy right first

---

### 3. react-uswds (US Web Design System for React)

**Context:** 216 stars, OSS license, TrussWorks maintains, WCAG 2.1 compliance built-in

#### Individual Assessments

**Crawdad (Security):** APPROVE
TrussWorks is reputable (government contractor, track record on civic tech). OSS license is clean. Dependency chain is standard React ecosystem (nothing exotic). Low supply chain risk. No phone-home concerns (it's UI components).

**Spider (Cultural Authority):** APPROVE WITH CONDITIONS
USWDS is designed for US government aesthetics. This is appropriate for VetAssist (VA system is US government). CONCERN: If we extend to TribeAssist (serving Cherokee Nation), US government branding may feel colonial. CONDITION: Must be theme-able. Cherokee Nation interface should not look like a federal website.

**Raven (Strategic):** APPROVE
Strong strategic alignment. Using government design standards gives us legitimacy when interfacing with VA systems. Accessibility compliance is not optional for us (many veterans have disabilities). This solves real problem.

**Turtle (Longevity):** APPROVE WITH CONDITIONS
216 stars is small community. TrussWorks is a consultancy: if they lose government contracts, do they abandon this? USWDS itself (non-React version) is maintained by GSA and will exist forever. React wrapper is the risk. CONDITION: Be prepared to fork and maintain if TrussWorks walks away.

**Gecko (Technical):** APPROVE
Code quality is good. API design follows React best practices. Integration is straightforward (drop-in components). Performance is fine (it's just CSS + React components). Better than building accessible components from scratch.

**Eagle Eye (Pattern Recognition):** APPROVE
No concerning patterns detected. This is civic tech done right: government design system, open-sourced, community-maintained. Small community is a risk but not a red flag.

#### Consensus Verdict: **APPROVE WITH CONDITIONS**

**Conditions:**
1. Must be theme-able for non-VA contexts (especially Cherokee Nation branding)
2. Fork and archive repository at integration time (longevity insurance)
3. Contribute accessibility improvements upstream (community health investment)

**Integration Priority:** High — Accessibility is non-negotiable

---

### 4. RJSF / react-jsonschema-form (Form Engine)

**Context:** 15.6k stars, Apache 2.0, auto-generates forms from JSON Schema, large community

#### Individual Assessments

**Crawdad (Security):** APPROVE
Apache 2.0 license is clean. Large community (15.6k stars) means many eyes on code. Dependency chain is reasonable. No phone-home concerns. Low supply chain risk.

**Spider (Cultural Authority):** APPROVE
Form generation is culturally neutral. Does not touch sensitive data processing (just UI rendering). No sovereignty concerns.

**Raven (Strategic):** HOLD FOR EVALUATION
This replaces our custom YAML wizard engine. That engine has institutional knowledge baked in (how we structure questions, how we guide veterans). Concern: are we trading flexibility for convenience? QUESTION: Can RJSF replicate our wizard UX (conditional fields, progress tracking, contextual help)?

**Turtle (Longevity):** APPROVE
15.6k stars is very healthy community. Multiple corporate sponsors. JSON Schema is W3C standard (will exist forever). This will exist in 7 years.

**Gecko (Technical):** APPROVE WITH CONDITIONS
Code quality is excellent. API is well-designed. Integration complexity is moderate: we'd need to convert YAML wizards to JSON Schema. CONDITION: Need proof-of-concept migration of one wizard before full commitment. Ensure we can replicate conditional logic, validation, and UX.

**Eagle Eye (Pattern Recognition):** APPROVE
No concerning patterns. This is mature open-source done right. Raven's concern about trading flexibility is valid but can be tested with POC.

#### Consensus Verdict: **APPROVE WITH CONDITIONS**

**Conditions:**
1. Proof-of-concept: Migrate one YAML wizard (e.g., VA-21-526EZ) to RJSF
2. Validate we can replicate: conditional fields, validation logic, progress tracking, contextual help
3. If POC succeeds, migrate incrementally (not big-bang replacement)

**Integration Priority:** Medium — Potential major improvement, but needs validation

---

### 5. PolicyEngine US (Benefits Microsimulation)

**Context:** 280+ stars, nonprofit-backed, full US benefits eligibility calculator

#### Individual Assessments

**Crawdad (Security):** HOLD FOR EVALUATION
280 stars is small community. "Verify license" flag in prompt suggests license is unclear. REQUIREMENT: Confirm license before proceeding. If AGPL: REJECT (copyleft incompatible with our mixed-license stack). If permissive: audit codebase for data exfiltration. Benefits calculation should not require external API calls.

**Spider (Cultural Authority):** APPROVE WITH CONDITIONS
Benefits calculation serves people. Concern: PolicyEngine is designed for policy advocacy (showing impact of policy changes). We're using it for individual calculation. Ensure we're not misusing the tool. CONDITION: Validate calculation accuracy against official SSA/VA calculators before trusting in production.

**Raven (Strategic):** APPROVE
Strong strategic alignment. Benefits calculation is HIGH value for veterans (many leave money on table). If this is accurate, it's a major competitive advantage. Concern: if PolicyEngine is nonprofit, what's their funding model? Will they sunset this project?

**Turtle (Longevity):** HOLD FOR EVALUATION
280 stars is small. Nonprofit backing is good but not guarantee of longevity. Need to investigate: Who funds this? What happens if funding dries up? Is there a succession plan?

**Gecko (Technical):** HOLD FOR EVALUATION
Need to evaluate: Does this run locally or require API calls? If API-dependent, REJECT (we can't rely on external service uptime for critical calculations). If local: evaluate performance and integration complexity.

**Eagle Eye (Pattern Recognition):** HOLD FOR EVALUATION
Pattern detected: Nonprofit-backed policy advocacy tool being repurposed for direct service. This is not inherently bad, but it's a mismatch. Policy tools optimize for "showing systemic impact" not "individual accuracy." Need to validate this is production-ready for individual calculations.

#### Consensus Verdict: **HOLD FOR EVALUATION**

**Required Before Integration:**
1. Confirm license (if AGPL: auto-reject)
2. Audit for data exfiltration / external API dependencies
3. Validate calculation accuracy against SSA/VA official calculators
4. Investigate funding model and longevity plan
5. Confirm tool is designed for individual calculation (not just policy modeling)

**Integration Priority:** High IF evaluation passes — This is high-value capability

---

### 6. Open Social Security (PIA Calculator)

**Context:** MIT license, Social Security claiming strategy optimization

#### Individual Assessments

**Crawdad (Security):** APPROVE WITH CONDITIONS
MIT license is clean. Concern: This appears to be individual contributor project (no org backing). Need to audit codebase size and complexity. If it's small and auditable: APPROVE. If it's large and complex: HOLD (can't trust individual contributor to maintain complex financial calculation logic).

**Spider (Cultural Authority):** APPROVE
Social Security calculation serves elders. Culturally appropriate. No sovereignty concerns.

**Raven (Strategic):** APPROVE
Social Security optimization is high value. Many veterans don't understand claiming strategies. This could save people tens of thousands of dollars over retirement. Strong mission alignment.

**Turtle (Longevity):** REJECT
Individual contributor project. No organizational backing. Social Security calculation logic changes with legislation. Who will maintain this when tax law changes? This will NOT exist in 7 years unless we maintain it.

**Gecko (Technical):** HOLD FOR EVALUATION
Need to evaluate code quality and complexity. If it's a simple PIA calculator (applying published formula): low maintenance burden, we can adopt and maintain. If it's complex optimization engine: too much maintenance burden for individual contributor project.

**Eagle Eye (Pattern Recognition):** HOLD FOR EVALUATION
Pattern detected: Individual contributor passion project in complex regulatory domain. High abandonment risk. However, if code is simple and well-documented, we could fork and maintain. Need to assess maintenance burden.

#### Consensus Verdict: **HOLD FOR EVALUATION**

**Required Before Integration:**
1. Audit codebase size and complexity
2. Validate calculation accuracy against SSA official calculators
3. Assess maintenance burden: Can we maintain this if contributor walks away?
4. If complexity is high: REJECT
5. If complexity is low and code is clear: APPROVE with plan to fork and maintain

**Integration Priority:** Medium — High value but high risk

---

### 7. axe-core (Accessibility Testing)

**Context:** Deque Systems, MPL 2.0, industry standard for WCAG testing

#### Individual Assessments

**Crawdad (Security):** APPROVE
MPL 2.0 license is clean (weak copyleft, compatible with our stack). Deque is reputable company with accessibility focus. Dependency chain is minimal. No security concerns.

**Spider (Cultural Authority):** APPROVE
Accessibility testing serves disabled people (many veterans, many Cherokee citizens). Culturally appropriate. No sovereignty concerns.

**Raven (Strategic):** APPROVE
Accessibility is non-negotiable. Automated testing in CI/CD prevents regressions. This is industry standard (using anything else would be reinventing wheel). Strong alignment.

**Turtle (Longevity):** APPROVE
Deque's entire business model is accessibility. This tool is their flagship open-source offering. Will exist in 7 years. Very low risk.

**Gecko (Technical):** APPROVE
Code quality is excellent. Integration is straightforward (npm package, CI/CD plugin). Performance is good (runs in seconds). This is best-in-class tool.

**Eagle Eye (Pattern Recognition):** APPROVE
No concerning patterns. Deque open-sources axe-core to drive adoption of their paid consulting/training services. This is sustainable business model. We benefit from free tool, they benefit from ecosystem growth. Aligned incentives.

#### Consensus Verdict: **APPROVE**

**No conditions required.**

**Integration Priority:** High — Integrate into CI/CD immediately

---

## TIER 2: Proposed for Evaluation

### 8. medspaCy / scispaCy (Clinical NLP)

**Context:** Medical entity extraction, negation detection, Allen AI (scispaCy), academic (medspaCy)

#### Individual Assessments

**Crawdad (Security):** HOLD FOR EVALUATION
Academic provenance is double-edged: good peer review, but poor maintenance. Need to evaluate: Are models trained on HIPAA-compliant data? Or did they scrape PubMed/clinical notes without consent? If models contain improperly sourced PHI: REJECT on ethical grounds.

**Spider (Cultural Authority):** HOLD FOR EVALUATION
Critical concern: Medical NLP trained on Western medicine will misclassify or ignore Indigenous healing practices. If we use this to extract "conditions" from veteran medical records, will it recognize traditional healing? Will it flag Cherokee medicine as "non-medical"? Need to evaluate cultural bias in training data.

**Raven (Strategic):** APPROVE WITH CONDITIONS
Medical entity extraction could accelerate claims processing (pulling conditions from records automatically). High value. But Spider's concern is valid: bias could harm Indigenous veterans. CONDITION: Must be tunable with custom entity types. Must be validated on Indigenous veteran records.

**Turtle (Longevity):** HOLD FOR EVALUATION
Academic projects have high abandonment risk. Allen AI has better track record than typical academic lab, but still risk. Need to evaluate: Is this maintained? When was last update?

**Gecko (Technical):** HOLD FOR EVALUATION
spaCy ecosystem is solid foundation. Need to evaluate integration complexity and model size (can we run locally?). If it requires external API: REJECT.

**Eagle Eye (Pattern Recognition):** HOLD FOR EVALUATION
Pattern detected: Academic NLP tools often trained on data scraped without consent, then open-sourced without acknowledging data provenance. This is extractive research practice. Need to audit data ethics before adopting.

#### Consensus Verdict: **HOLD FOR EVALUATION**

**Required Before Integration:**
1. Audit training data provenance (is it ethically sourced?)
2. Evaluate cultural bias (does it recognize Indigenous healing practices?)
3. Confirm local deployment (no external APIs)
4. Assess maintenance status (is it abandoned?)
5. Validate we can add custom entity types for Cherokee/Indigenous context

**Integration Priority:** Low — High value but high risk of cultural harm

---

### 9. Electronic CFR on GitHub (Pre-processed CFR Data)

**Context:** Entire Code of Federal Regulations for RAG ingestion, individual contributor maintains

#### Individual Assessments

**Crawdad (Security):** APPROVE WITH CONDITIONS
Individual contributor is risk, but CFR is public domain data. Concern: Is this data scraped correctly? Are there errors introduced in processing? CONDITION: Validate subset of CFR data against official e-CFR.gov before trusting.

**Spider (Cultural Authority):** APPROVE
CFR is public law. No sovereignty concerns. Using processed version is practical (official e-CFR is XML hell).

**Raven (Strategic):** APPROVE
CFR data is critical for VetAssist (38 CFR governs VA benefits). Having clean, RAG-ready version saves significant processing time. Strong alignment.

**Turtle (Longevity):** APPROVE WITH CONDITIONS
Individual contributor is risk. CFR updates regularly (federal register publishes changes). CONDITION: We must build our own update pipeline. Cannot rely on contributor to keep this current. Use this as bootstrap, build sustainability.

**Gecko (Technical):** APPROVE WITH CONDITIONS
Need to evaluate data format and quality. If it's clean JSON/markdown: excellent. If it's weird custom format: not worth it. CONDITION: Validate format before committing to use.

**Eagle Eye (Pattern Recognition):** APPROVE WITH CONDITIONS
Pattern detected: Individual solving their own problem, sharing solution. This is authentic open source. Risk is sustainability. Recommendation: Use this as starting point, take ownership of data pipeline.

#### Consensus Verdict: **APPROVE WITH CONDITIONS**

**Conditions:**
1. Validate data accuracy against official e-CFR.gov (sample-based audit)
2. Fork and archive data at integration time
3. Build our own CFR update pipeline (do not depend on contributor)
4. Validate data format is usable for RAG

**Integration Priority:** High — Critical data source for VetAssist

---

### 10. Together MoA (Mixture of Agents)

**Context:** Multi-agent debate architecture, Together AI corporate backing

#### Individual Assessments

**Crawdad (Security):** REJECT
Together AI is API-first company. This likely requires external API calls to Together's infrastructure. If so: REJECT (we don't send user data to external services). If it's fully local: HOLD FOR EVALUATION.

**Spider (Cultural Authority):** REJECT
Together AI is venture-backed startup. Their business model is selling API access. This is extractive: they want our usage data to improve their models. Our veterans' deliberations should not train their commercial models.

**Raven (Strategic):** REJECT
We already have council architecture. We don't need external validation. Using Together's framework creates dependency and exposes our design to competitors. No strategic value.

**Turtle (Longevity):** REJECT
Venture-backed startup. Will this exist in 7 years? Unknown. Will they pivot away from open source if it doesn't drive revenue? High risk.

**Gecko (Technical):** HOLD FOR EVALUATION
MoA architecture is interesting research. But need to evaluate: Is this actually better than our council? Or is it just hype? If there's genuine technical merit AND it runs fully local: worth evaluating.

**Eagle Eye (Pattern Recognition):** REJECT
Pattern detected: VC-backed company open-sourcing "framework" to drive API adoption. This is loss-leader strategy. They want us to prototype locally, then hit scale and "upgrade" to their API. Classic lock-in pattern. Hard reject.

#### Consensus Verdict: **REJECT**

**Rationale:** Extractive business model, creates dependency, no clear advantage over our existing council architecture, high lock-in risk.

**Integration Priority:** N/A — Rejected

---

### 11. MentalLLaMA (Mental Health Analysis LLM)

**Context:** Open-source crisis detection model, academic research origin

#### Individual Assessments

**Crawdad (Security):** HOLD FOR EVALUATION
Academic origin is double-edged. Need to evaluate: Training data provenance? Is this trained on scraped social media posts (ethical violation)? License terms? Model size (can we run locally)?

**Spider (Cultural Authority):** HOLD FOR EVALUATION
Crisis detection for veterans is culturally appropriate. CONCERN: Is this trained on Indigenous mental health data? Is Western mental health framework being imposed? Many Cherokee veterans experience historical trauma: will this model understand that context or pathologize it?

**Raven (Strategic):** HOLD FOR EVALUATION
Crisis detection is high value and high risk. If we get false positives, we traumatize people. If we get false negatives, people die. This is not a place for experimental academic models. Need to evaluate: What's the accuracy? What's the false positive rate? What's the validation methodology?

**Turtle (Longevity):** REJECT
Academic research models are published for citations, not maintenance. This will be abandoned after the paper is published. If we integrate, we own maintenance forever in safety-critical domain. Too much risk.

**Gecko (Technical):** HOLD FOR EVALUATION
Need to evaluate model size, inference speed, and whether it runs locally. If it requires external API: auto-reject. Need to evaluate accuracy on veteran population specifically.

**Eagle Eye (Pattern Recognition):** REJECT
Pattern detected: Academic researchers publish model for paper, cite "open source" for ethics points, never maintain it. This is research extraction disguised as contribution. Crisis detection is too important to rely on abandoned research model.

#### Consensus Verdict: **REJECT**

**Rationale:** Safety-critical domain, academic abandonment risk, unknown cultural bias, unknown training data ethics. Risk exceeds value.

**Alternative:** Build our own crisis detection using C-SSRS protocol + RoBERTa (which we control and validate).

**Integration Priority:** N/A — Rejected, use internal alternative

---

### 12. CrewAI (Role-Based Autonomous Agents)

**Context:** 100k+ developer community, role-based agent orchestration

#### Individual Assessments

**Crawdad (Security):** HOLD FOR EVALUATION
100k+ community is strong signal. Need to evaluate: License terms? Dependency chain? Does it phone home? Is there telemetry? If clean: worth evaluating.

**Spider (Cultural Authority):** APPROVE WITH CONDITIONS
Agent orchestration is culturally neutral. CONDITION: If we use this to replace Jr executor, we must ensure Jr names and personas are preserved (Cherokee/cultural identity is important).

**Raven (Strategic):** HOLD FOR EVALUATION
Interesting question: Does CrewAI simplify our Jr executor architecture or does it impose someone else's framework? Need to evaluate: Can we replicate our current Jr capabilities? Do we gain meaningful simplification or just trade one complexity for another?

**Turtle (Longevity):** APPROVE
100k+ community is very healthy. Multiple contributors. This will exist in 7 years.

**Gecko (Technical):** HOLD FOR EVALUATION
Need to evaluate: Integration complexity vs. benefit. Our Jr executor works. Is CrewAI better enough to justify migration cost? Need proof-of-concept comparison.

**Eagle Eye (Pattern Recognition):** HOLD FOR EVALUATION
Pattern detected: Rapid growth (100k+ community) suggests either genuine utility or hype cycle. Need to distinguish. If this is hype, it will crash. If it's utility, it's worth considering.

#### Consensus Verdict: **HOLD FOR EVALUATION**

**Required Before Integration:**
1. Security audit (license, dependencies, telemetry)
2. Proof-of-concept: Replicate one Jr executor task with CrewAI
3. Evaluate whether it simplifies or complicates our architecture
4. Assess migration cost vs. benefit

**Integration Priority:** Low — Current system works, this is optimization not necessity

---

### 13. Legal_Medical_RAG (Dual-Domain RAG)

**Context:** Legal + medical document RAG pipeline, individual contributor

#### Individual Assessments

**Crawdad (Security):** HOLD FOR EVALUATION
Individual contributor is risk. Need to audit codebase for: License, dependencies, security vulnerabilities, data handling practices. If code quality is poor: reject (not worth risk).

**Spider (Cultural Authority):** APPROVE WITH CONDITIONS
Dual-domain RAG (legal + medical) is exactly our use case (VA claims require both). CONDITION: Must be tunable with our CFR data and our medical entity extraction. Cannot be black box.

**Raven (Strategic):** HOLD FOR EVALUATION
This could be useful reference architecture. But concern: Individual contributor project may not be production-quality. Need to evaluate: Is this research demo or production code?

**Turtle (Longevity):** REJECT
Individual contributor, no organizational backing, complex system. This will be abandoned. If we use it, we own it forever. For reference architecture: fine. For production dependency: reject.

**Gecko (Technical):** HOLD FOR EVALUATION
Need to evaluate code quality and architecture. If it's clean and well-documented: useful as reference. If it's messy: not worth time. If it's production-quality: surprising (individual contributor rarely produces production-quality complex systems alone).

**Eagle Eye (Pattern Recognition):** HOLD FOR EVALUATION
Pattern detected: Individual contributor solving their own problem, sharing solution. This is authentic open source. But scale of problem (dual-domain RAG) suggests this is likely thesis project or portfolio piece, not production system. Treat as reference, not dependency.

#### Consensus Verdict: **HOLD FOR EVALUATION**

**Required Before Integration:**
1. Audit code quality and architecture
2. Evaluate whether it's production-ready or research demo
3. If research demo: use as reference architecture, do not depend on it
4. If production-ready: validate on our use cases, then consider adoption

**Integration Priority:** Low — Treat as reference unless evaluation reveals production quality

---

## FINAL COUNCIL RECOMMENDATION

### APPROVED FOR IMMEDIATE INTEGRATION

1. **axe-core** — No conditions. Integrate into CI/CD immediately.
2. **react-uswds** — Approved with conditions (theme-ability, fork for longevity).
3. **IBM Docling** — Approved with conditions (self-host, no IBM cloud, FPIC consent, abstraction layer).

### APPROVED PENDING PROOF-OF-CONCEPT

4. **RJSF** — Migrate one wizard, validate UX replication, then proceed.
5. **Electronic CFR** — Validate data accuracy, fork, build update pipeline.

### HOLD FOR EVALUATION (High Priority)

6. **PolicyEngine US** — IF license is permissive AND runs locally AND calculations validate: High value. Requires investigation.
7. **Open Social Security** — IF codebase is simple AND we can maintain: High value. Requires complexity assessment.

### HOLD FOR EVALUATION (Medium Priority)

8. **Microsoft Presidio** — Philosophy misalignment (redaction vs. sovereignty). Requires cultural alignment work before technical integration.
9. **medspaCy/scispaCy** — Cultural bias risk. Requires data ethics audit and cultural validation.

### HOLD FOR EVALUATION (Low Priority)

10. **CrewAI** — Current system works. Evaluate only if bandwidth allows.
11. **Legal_Medical_RAG** — Treat as reference architecture unless proven production-quality.

### REJECTED

12. **Together MoA** — Extractive business model, lock-in risk, no advantage over existing council.
13. **MentalLLaMA** — Safety-critical domain, academic abandonment risk, use internal alternative.

---

## INTEGRATION PRINCIPLES (Seven Generations Thinking)

The council reaffirms these principles for all technology adoption:

1. **Sovereignty First** — No tool may require sending user data to external services.
2. **Cultural Integrity** — Tools trained on Western data must be validated for cultural bias before use with Indigenous populations.
3. **Longevity Over Convenience** — Individual contributor projects require fork-and-maintain plan.
4. **Consent Over Compliance** — Redaction and AI processing require explicit user consent (FPIC), not just legal compliance.
5. **Mission Alignment** — Every tool must serve people, not extract from them.
6. **Escape Velocity** — Every dependency must have exit strategy (abstraction layers, forks, alternatives).
7. **Community Investment** — When we benefit from open source, we contribute back (upstream improvements, documentation, bug fixes).

---

## NEXT ACTIONS

### For TPM:
1. Write Jr instructions for approved integrations (axe-core, react-uswds, IBM Docling)
2. Commission proof-of-concept tasks (RJSF wizard migration, Electronic CFR validation)
3. Assign evaluation tasks for HOLD items (PolicyEngine license check, Open Social Security complexity audit, etc.)

### For Crawdad:
1. Security audit: Microsoft Presidio (telemetry check)
2. Security audit: PolicyEngine US (license confirmation, API dependency check)
3. Security audit: medspaCy/scispaCy (training data provenance)

### For Spider:
1. Cultural alignment assessment: Microsoft Presidio redaction philosophy
2. Cultural bias evaluation: medspaCy/scispaCy on Indigenous medical context
3. Design specification: User-controlled redaction with FPIC consent model

### For Gecko:
1. Proof-of-concept: Migrate VA-21-526EZ wizard to RJSF
2. Code audit: Open Social Security (complexity assessment)
3. Architecture review: IBM Docling integration pattern

### For Turtle:
1. Longevity research: PolicyEngine funding model and succession plan
2. Maintenance assessment: Open Social Security (can we maintain if contributor leaves?)

### For Raven:
1. Strategic analysis: Does RJSF maintain our UX competitive advantage?
2. Strategic analysis: PolicyEngine accuracy validation methodology

### For Eagle Eye:
1. Pattern analysis: CrewAI (hype vs. utility?)
2. Risk assessment: What are we missing? (Open floor for additional concerns)

---

## COUNCIL VOTE RECORD

**Approved:** 3 tools (axe-core, react-uswds, IBM Docling)
**Approved Pending POC:** 2 tools (RJSF, Electronic CFR)
**Hold for Evaluation:** 6 tools (PolicyEngine, Open Social Security, Presidio, medspaCy/scispaCy, CrewAI, Legal_Medical_RAG)
**Rejected:** 2 tools (Together MoA, MentalLLaMA)

**Consensus:** Unanimous on rejections. Unanimous on axe-core approval. Conditional approval for others reflects rigor: we do not compromise integrity for convenience.

**Cultural Note:** Spider's interventions on Presidio (redaction philosophy) and medspaCy (cultural bias) demonstrate why Indigenous representation on technical councils is not optional. These concerns would have been invisible to non-Indigenous technologists.

**Seven Generations Commitment:** Every approved tool includes either exit strategy (abstraction layer, fork plan) or low-risk profile (small, auditable, maintainable). We are building for 7 years, not 7 months.

---

**Council Session Closed:** February 4, 2026
**Next Review:** Quarterly technology stack assessment (May 2026)

ᏩᏙ (It is finished.)
