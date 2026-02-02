# Jr Instruction: Seed VetAssist Educational Content (Corrected Schema)

**Task ID:** VETASSIST-SEED-CONTENT-002
**Assigned To:** Software Engineer Jr
**Priority:** P0 — Resources page has no content
**Created:** January 31, 2026
**Depends On:** VETASSIST-RESOURCES-FIX-001 (backend tags fix must be deployed first)
**Estimated Steps:** 3

---

## Objective

Populate the `educational_content` table with 17 educational articles about VA disability claims. The resources page is currently empty (1 test row). Veterans need real content to build trust in the platform.

---

## CRITICAL Schema Notes

The previous seed instruction (Jan 30) had wrong schema assumptions. The ACTUAL schema is:

| Column | Actual Type | NOT what was assumed |
|--------|-------------|---------------------|
| id | **varchar** (UUID) | NOT serial/integer |
| tags | **text** (JSON string) | NOT text[] (PostgreSQL array) |
| view_count | integer | nullable, no default |
| created_at | timestamptz | nullable, no default |
| updated_at | timestamptz | nullable, no default |

**Tags must be stored as JSON strings**, e.g., `'["claims", "basics", "getting-started"]'` — NOT PostgreSQL array syntax.

**IDs must be UUIDs**, e.g., generated with `uuid.uuid4()`.

---

## Steps

### Step 1: Create the seed script

**File:** `/ganuda/vetassist/backend/scripts/seed_educational_content.py`

```python
#!/usr/bin/env python3
"""
Seed educational content for VetAssist resources page.
Idempotent: skips articles where slug already exists.

Usage:
    cd /ganuda/vetassist/backend
    ./venv/bin/python scripts/seed_educational_content.py
"""

import uuid
import json
import psycopg2
from datetime import datetime, timezone

DB_CONFIG = {
    'host': '192.168.132.222',
    'dbname': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

ARTICLES = [
    # === BEGINNER LEVEL ===
    {
        'title': 'Understanding VA Disability Claims',
        'slug': 'understanding-va-disability-claims',
        'content_type': 'article',
        'difficulty_level': 'beginner',
        'estimated_read_time': 8,
        'tags': json.dumps(['claims', 'basics', 'getting-started']),
        'summary': 'A complete overview of the VA disability claims process — what it is, who qualifies, and how to get started.',
        'content': """## Understanding VA Disability Claims

If you served in the military and have a health condition related to your service, you may be eligible for VA disability compensation. This is a tax-free monthly payment that recognizes the impact of service-connected conditions on your life.

### Key Points

- VA disability compensation is available to veterans with conditions caused or worsened by military service
- You do not need to have been injured in combat to qualify
- Both physical and mental health conditions can be claimed
- You can file a claim at any time after discharge — there is no deadline

### What Is a Service-Connected Disability?

A service-connected disability is any illness, injury, or condition that was caused by or worsened during your active military service. This includes:

- **Direct service connection**: An injury or illness that occurred during service (e.g., hearing loss from weapons training)
- **Aggravated conditions**: A pre-existing condition that worsened during service
- **Secondary conditions**: A new condition caused by an already service-connected condition (e.g., depression caused by chronic pain from a service-connected back injury)

### The Claims Process Overview

1. **Gather evidence**: Collect service records, medical records, and supporting statements
2. **File your claim**: Submit VA Form 21-526EZ online, by mail, or with a VSO's help
3. **C&P Examination**: VA may schedule a Compensation & Pension exam
4. **VA Review**: A rating specialist reviews all evidence
5. **Decision**: You receive a rating decision with your disability percentage

### What to Do Next

- Create your VetAssist account to use our free disability calculator
- Gather your DD-214 (discharge papers) and medical records
- Consider connecting with a Veterans Service Organization (VSO) for free help

---

*This is educational information only, not legal advice. Consult a VA-accredited representative for guidance specific to your situation.*"""
    },
    {
        'title': 'How VA Disability Ratings Work',
        'slug': 'how-va-disability-ratings-work',
        'content_type': 'article',
        'difficulty_level': 'beginner',
        'estimated_read_time': 6,
        'tags': json.dumps(['ratings', 'calculator', 'basics']),
        'summary': 'Learn how VA calculates your combined disability rating — and why 50% + 30% does not equal 80%.',
        'content': """## How VA Disability Ratings Work

One of the most confusing aspects of VA disability is how ratings are calculated. The VA uses a specific formula called "combined ratings" that works differently than simple addition.

### Key Points

- Disability ratings range from 0% to 100% in increments of 10%
- Multiple ratings are combined using VA math, not simple addition
- Your combined rating determines your monthly compensation amount
- Ratings can be increased if your condition worsens

### VA Math Explained

The VA calculates combined ratings based on your remaining "whole person" efficiency. Here's how it works:

**Example: 50% + 30%**
1. Start with 100% (whole person)
2. Apply the 50% rating: 100% × 50% = 50% disabled, 50% remaining
3. Apply the 30% rating to what remains: 50% × 30% = 15% additional disability
4. Total: 50% + 15% = 65%, rounded to **70%**

This is why 50% + 30% = 70%, not 80%.

### The Bilateral Factor

If you have disabilities affecting both arms, both legs, or paired extremities, the VA applies a "bilateral factor" — a small bonus (usually 1-3%) that increases your combined rating.

### What to Do Next

- Use the VetAssist disability calculator to estimate your combined rating
- Review your current rating decision letter for accuracy
- If your conditions have worsened, consider filing for an increased rating

---

*This is educational information only, not legal advice. Consult a VA-accredited representative for guidance specific to your situation.*"""
    },
    {
        'title': 'Types of VA Disability Claims',
        'slug': 'types-of-va-disability-claims',
        'content_type': 'article',
        'difficulty_level': 'beginner',
        'estimated_read_time': 7,
        'tags': json.dumps(['claims', 'types', 'basics']),
        'summary': 'Original claims, increased ratings, secondary conditions, and TDIU — understand which type of claim is right for you.',
        'content': """## Types of VA Disability Claims

Not all VA claims are the same. Understanding which type to file is crucial for a successful outcome.

### Key Points

- There are several types of claims, each with different requirements
- You can file multiple types of claims at the same time
- Choosing the right claim type affects what evidence you need

### Original Claim

Your first-ever claim for disability compensation. Filed on VA Form 21-526EZ. You need to establish that your condition is connected to military service.

### Claim for Increase

If an already service-connected condition has gotten worse, you can file for an increased rating. You'll need current medical evidence showing the worsening.

### Secondary Service Connection

A new condition caused by an already service-connected disability. For example:
- Sleep apnea secondary to PTSD
- Radiculopathy secondary to a back condition
- Depression secondary to chronic pain

You need a medical nexus opinion linking the secondary condition to the primary one.

### Total Disability Based on Individual Unemployability (TDIU)

If your service-connected disabilities prevent you from maintaining substantially gainful employment, you may qualify for TDIU — which pays at the 100% rate even if your combined rating is lower.

### What to Do Next

- Identify which type of claim matches your situation
- Use VetAssist's guided wizard to help determine the right approach
- Gather condition-specific evidence before filing

---

*This is educational information only, not legal advice. Consult a VA-accredited representative for guidance specific to your situation.*"""
    },
    {
        'title': 'Evidence You Need for Your VA Claim',
        'slug': 'evidence-you-need-for-va-claim',
        'content_type': 'article',
        'difficulty_level': 'beginner',
        'estimated_read_time': 10,
        'tags': json.dumps(['evidence', 'documentation', 'basics']),
        'summary': 'Service records, medical records, buddy statements, and nexus letters — what evidence the VA needs and how to get it.',
        'content': """## Evidence You Need for Your VA Claim

The strength of your VA claim depends almost entirely on the evidence you submit. Understanding what the VA needs can make the difference between approval and denial.

### Key Points

- The VA decides claims based on the "preponderance of evidence" standard
- You need three things: a current diagnosis, an in-service event, and a medical nexus
- More evidence is almost always better than less
- The VA has a "duty to assist" but you should not rely on it alone

### The Three Pillars of Evidence

**1. Current Diagnosis**
Medical records showing you currently have the condition you're claiming. Recent records (within the last year) are most persuasive.

**2. In-Service Event or Exposure**
Proof that something happened during your service that caused or contributed to your condition. This can include service treatment records, personnel records, unit histories, or buddy statements.

**3. Medical Nexus**
A medical opinion connecting your current condition to your in-service event. This is often the most critical piece — and the one most commonly missing from denied claims.

### Types of Evidence

- **Service Treatment Records (STRs)**: Medical records from during your service
- **VA Medical Records**: Treatment records from VA facilities
- **Private Medical Records**: Records from civilian doctors
- **Nexus Letters**: A doctor's opinion linking your condition to service
- **Buddy Statements (VA Form 21-4138)**: Statements from fellow service members or family
- **DD-214**: Your discharge document showing service dates and conditions

### What to Do Next

- Request your complete service records from the National Personnel Records Center
- Get a current diagnosis from your doctor for each condition
- Ask your doctor if they can provide a nexus opinion
- Upload your documents to VetAssist for AI-powered gap analysis

---

*This is educational information only, not legal advice. Consult a VA-accredited representative for guidance specific to your situation.*"""
    },
    {
        'title': 'The VA Claims Timeline: What to Expect',
        'slug': 'va-claims-timeline',
        'content_type': 'article',
        'difficulty_level': 'beginner',
        'estimated_read_time': 5,
        'tags': json.dumps(['timeline', 'process', 'basics']),
        'summary': 'From filing to decision — understand the typical timeline and stages of a VA disability claim.',
        'content': """## The VA Claims Timeline: What to Expect

One of the most common questions veterans have is "how long will my claim take?" While every claim is different, understanding the typical timeline helps set expectations.

### Key Points

- The average VA claim takes 3-6 months from filing to decision
- Complex claims or appeals can take significantly longer
- You can check your claim status online at VA.gov
- Filing a Fully Developed Claim (FDC) can speed up the process

### Stages of a VA Claim

**1. Claim Received (Week 1)**
The VA acknowledges receipt of your claim and assigns it a tracking number.

**2. Under Review (Weeks 2-8)**
A Veterans Service Representative reviews your claim and requests any missing evidence.

**3. Gathering Evidence (Weeks 4-16)**
The VA collects your service records, medical records, and any other evidence. They may schedule a C&P exam during this phase.

**4. Review of Evidence (Weeks 12-20)**
A Rating Veterans Service Representative reviews all evidence and makes a decision.

**5. Preparation for Decision (Weeks 16-24)**
The decision is finalized and a notification letter is prepared.

**6. Decision (Complete)**
You receive your rating decision letter explaining the outcome and your rating percentage.

### How to Speed Up Your Claim

- File a Fully Developed Claim with all evidence included upfront
- Respond quickly to any VA requests for additional information
- Attend all scheduled C&P exams
- Keep copies of everything you submit

### What to Do Next

- Track your claim status at VA.gov
- Use VetAssist to organize your evidence before filing
- Set up direct deposit for faster payment if approved

---

*This is educational information only, not legal advice. Consult a VA-accredited representative for guidance specific to your situation.*"""
    },
    {
        'title': 'Getting Started with VetAssist',
        'slug': 'getting-started-with-vetassist',
        'content_type': 'guide',
        'difficulty_level': 'beginner',
        'estimated_read_time': 4,
        'tags': json.dumps(['vetassist', 'tutorial', 'getting-started']),
        'summary': 'A quick guide to using VetAssist — the disability calculator, AI chat, dashboard, and claims wizard.',
        'content': """## Getting Started with VetAssist

VetAssist is a free AI-powered platform designed to help veterans understand and navigate VA disability claims. Here's how to make the most of it.

### Key Features

**Disability Rating Calculator**
Enter your conditions and get an estimated combined VA disability rating using the same math the VA uses. See how adding or increasing conditions affects your overall rating.

**AI Claims Assistant**
Chat with our AI assistant about your specific situation. Ask questions about eligibility, evidence requirements, or claim strategies. The AI is trained on VA regulations (38 CFR) and current case law.

**Document Upload & Analysis**
Upload your medical records, service records, and other documents. Our AI analyzes them for evidence gaps and suggests what additional documentation you might need.

**Claims Dashboard**
Track your claims, organize your evidence, and manage your VetAssist account from one central location.

### Getting Started

1. **Create an account** — You just need an email address. No VA.gov account required.
2. **Try the calculator** — Enter your conditions to see your estimated rating
3. **Chat with the AI** — Ask any question about VA disability claims
4. **Upload documents** — Let our AI find evidence gaps in your records
5. **Link your VA.gov account** (optional) — Connect your VA.gov account later from Settings for additional features

### What to Do Next

- Explore the calculator to understand your potential rating
- Ask the AI assistant about your specific conditions
- Upload your DD-214 and medical records for analysis

---

*VetAssist is an educational tool, not a substitute for professional legal advice. For help with your specific claim, consult a VA-accredited representative.*"""
    },
    # === INTERMEDIATE LEVEL ===
    {
        'title': 'Understanding PTSD Claims',
        'slug': 'understanding-ptsd-claims',
        'content_type': 'article',
        'difficulty_level': 'intermediate',
        'estimated_read_time': 12,
        'tags': json.dumps(['ptsd', 'mental-health', 'claims']),
        'summary': 'How PTSD claims work — diagnostic criteria, stressor verification, and what to expect at your C&P exam.',
        'content': """## Understanding PTSD Claims

PTSD (Post-Traumatic Stress Disorder) is one of the most commonly claimed conditions for VA disability. Understanding the specific requirements for PTSD claims is essential for a successful outcome.

### Key Points

- PTSD claims have specific stressor verification requirements
- The VA recognizes combat, MST, and non-combat stressors
- PTSD ratings range from 0% to 100% based on symptom severity
- A current PTSD diagnosis from a qualified professional is required

### PTSD Stressor Categories

**Combat-Related Stressors**
If you served in a combat zone (confirmed by your DD-214 or service records), the VA will generally concede the stressor without additional proof.

**Military Sexual Trauma (MST)**
The VA has relaxed evidence requirements for MST claims. Evidence can include:
- Changes in behavior documented in service records
- Requests for transfer
- Counseling records
- Buddy statements

**Non-Combat Stressors**
Events like vehicle accidents, training injuries, or witnessing death require corroborating evidence from service records or buddy statements.

### PTSD Rating Criteria

| Rating | Symptoms |
|--------|----------|
| 0% | Diagnosed but symptoms controlled by medication |
| 10% | Mild symptoms with occasional decrease in work efficiency |
| 30% | Occasional decrease in work efficiency with depressed mood and anxiety |
| 50% | Reduced reliability with difficulty in social and work situations |
| 70% | Deficiencies in most areas — work, family, judgment, thinking, mood |
| 100% | Total occupational and social impairment |

### C&P Exam Tips for PTSD

- Be honest about your worst days, not just your average days
- Describe how symptoms affect your daily life, work, and relationships
- Mention sleep disturbances, nightmares, hypervigilance, and avoidance behaviors
- Bring a written list of symptoms — it's easy to forget things under stress

### What to Do Next

- Get a current PTSD diagnosis if you don't have one
- Document your stressor events with as much detail as possible
- Consider a private nexus letter if your treatment records are limited
- Use VetAssist's AI to help you understand your PTSD rating criteria

---

*This is educational information only, not legal advice. Consult a VA-accredited representative for guidance specific to your situation.*"""
    },
    {
        'title': 'Secondary Service Connection Explained',
        'slug': 'secondary-service-connection-explained',
        'content_type': 'article',
        'difficulty_level': 'intermediate',
        'estimated_read_time': 8,
        'tags': json.dumps(['secondary', 'claims', 'strategy']),
        'summary': 'How one service-connected condition can lead to claims for related conditions — and why this strategy matters.',
        'content': """## Secondary Service Connection Explained

Secondary service connection is one of the most powerful strategies in VA disability claims. It allows you to claim conditions that were caused or aggravated by an already service-connected disability.

### Key Points

- A secondary condition must be caused OR worsened by a primary service-connected condition
- You need a medical nexus opinion linking the conditions
- Secondary claims can significantly increase your combined rating
- Many veterans miss secondary conditions they could be claiming

### How Secondary Connection Works

If you have a service-connected knee injury and develop a limp that causes a hip condition, the hip condition is "secondary" to the knee. The VA recognizes this causal chain.

**The legal standard**: The secondary condition must be "proximately due to or the result of" a service-connected condition (38 CFR 3.310).

### Common Secondary Connections

| Primary Condition | Common Secondary Conditions |
|------|------|
| PTSD | Depression, anxiety, sleep apnea, migraines |
| Back injury | Radiculopathy, sciatica, hip conditions |
| Knee injury | Hip conditions, back conditions, opposite knee |
| Diabetes | Peripheral neuropathy, erectile dysfunction, vision problems |
| Hearing loss | Tinnitus (and vice versa) |

### Evidence Required

1. **Current diagnosis** of the secondary condition
2. **Medical nexus opinion** linking the secondary to the primary condition
3. **Medical records** showing treatment for both conditions

The nexus opinion is the most critical piece. It should clearly state: "It is at least as likely as not that [secondary condition] was caused by or aggravated by [primary condition]."

### What to Do Next

- Review your service-connected conditions and research common secondary connections
- Ask your doctor about conditions that may be related to your service-connected disabilities
- Use VetAssist to identify potential secondary claims you may be missing

---

*This is educational information only, not legal advice. Consult a VA-accredited representative for guidance specific to your situation.*"""
    },
    {
        'title': 'The C&P Exam: Preparation Guide',
        'slug': 'cp-exam-preparation-guide',
        'content_type': 'guide',
        'difficulty_level': 'intermediate',
        'estimated_read_time': 10,
        'tags': json.dumps(['c-and-p', 'exam', 'preparation']),
        'summary': 'What happens during a Compensation & Pension exam, how to prepare, and what mistakes to avoid.',
        'content': """## The C&P Exam: Preparation Guide

The Compensation & Pension (C&P) exam is often the most important step in your VA claim. The examiner's report carries significant weight in the rating decision.

### Key Points

- The C&P exam is NOT a treatment appointment — it's an evaluation
- The examiner writes a report that the rating specialist uses to make decisions
- You should describe your worst days, not your best days
- Missing a C&P exam can result in your claim being denied

### Before the Exam

1. **Review your medical records** and know your diagnosis
2. **Write down your symptoms** — including frequency, severity, and duration
3. **Document how symptoms affect daily life** — work, sleep, relationships, hobbies
4. **Bring a list of medications** and their side effects
5. **Bring a buddy or spouse** who can speak to how your condition affects you (if allowed to wait in the lobby)

### During the Exam

- Be honest and thorough — don't minimize or exaggerate
- Describe your worst days, not just your average
- If something hurts during a range-of-motion test, say so
- If you don't remember something, say "I don't recall" rather than guessing
- The examiner may ask about your daily routine — be specific about limitations

### Common Mistakes to Avoid

- **Minimizing symptoms**: "It's not that bad" or "I push through it"
- **Being too brief**: Provide details, not just yes/no answers
- **Missing the exam**: If you must reschedule, call immediately
- **Not mentioning flare-ups**: If your condition has good and bad days, describe both

### What to Do Next

- If you have a C&P exam scheduled, prepare using the checklist above
- Ask VetAssist's AI about specific exam criteria for your conditions
- Review the DBQ (Disability Benefits Questionnaire) form for your condition

---

*This is educational information only, not legal advice. Consult a VA-accredited representative for guidance specific to your situation.*"""
    },
    {
        'title': 'Buddy Statements That Win Claims',
        'slug': 'buddy-statements-that-win-claims',
        'content_type': 'guide',
        'difficulty_level': 'intermediate',
        'estimated_read_time': 7,
        'tags': json.dumps(['evidence', 'buddy-statements', 'writing']),
        'summary': 'How to write effective lay statements that strengthen your VA claim — with examples of what works.',
        'content': """## Buddy Statements That Win Claims

Buddy statements (lay statements) are written accounts from people who can support your claim. They're especially valuable when service records are incomplete or unavailable.

### Key Points

- Buddy statements are submitted on VA Form 21-4138 (Statement in Support of Claim)
- They can come from fellow service members, family, friends, coworkers, or you
- First-hand observations are more powerful than general statements
- Specific details (dates, locations, incidents) add credibility

### Who Can Write a Buddy Statement?

- Fellow service members who witnessed events or your condition
- Spouse, family members, or friends who observe your symptoms
- Coworkers who can speak to how your condition affects your work
- You (a personal statement describing your experiences)

### What Makes a Strong Buddy Statement

**Include:**
- Full name, relationship to the veteran, and contact information
- Specific dates, locations, and events when possible
- First-hand observations of symptoms or incidents
- How the veteran's condition has changed over time
- Impact on daily life, work, and relationships

**Avoid:**
- Medical diagnoses (unless the writer is a medical professional)
- Vague or general statements without specifics
- Copy-pasting the same statement from multiple people
- Emotional appeals without factual content

### Example Structure

> I, [Full Name], am writing to support [Veteran Name]'s claim for [condition]. I served with [him/her] at [unit/location] from [dates]. During our service, I personally observed [specific event/symptom]. Since [his/her] discharge, I have noticed [specific changes in behavior/ability]. These changes affect [his/her] daily life by [specific examples].

### What to Do Next

- Identify 2-3 people who can write statements supporting your claim
- Share the guidelines above with them
- Upload completed statements to VetAssist for inclusion in your claim package

---

*This is educational information only, not legal advice. Consult a VA-accredited representative for guidance specific to your situation.*"""
    },
    {
        'title': 'Understanding Your VA Decision Letter',
        'slug': 'understanding-va-decision-letter',
        'content_type': 'article',
        'difficulty_level': 'intermediate',
        'estimated_read_time': 9,
        'tags': json.dumps(['decision', 'ratings', 'process']),
        'summary': 'How to read your VA rating decision letter — what the codes mean and what your options are.',
        'content': """## Understanding Your VA Decision Letter

When the VA makes a decision on your claim, you'll receive a letter explaining the outcome. This letter contains critical information about your rating, effective date, and appeal rights.

### Key Points

- Your decision letter contains your rating percentage for each condition
- The effective date determines when your compensation payments begin
- You have one year to appeal if you disagree with the decision
- Understanding the letter is the first step in deciding your next move

### Key Sections of the Decision Letter

**1. Rating Decision**
Lists each claimed condition, the assigned rating percentage, and whether it was granted or denied.

**2. Effective Date**
The date from which your compensation is calculated. This is usually:
- Date of claim filing (most common)
- Date entitlement arose (if later than filing)
- Day after discharge (if filed within 1 year of separation)

**3. Combined Rating**
Your overall combined disability rating after VA math is applied.

**4. Monthly Compensation Amount**
The dollar amount you'll receive based on your combined rating and number of dependents.

**5. Appeal Rights**
Your options for challenging the decision, including deadlines.

### Common Decision Codes

- **Service Connected**: Your condition was linked to military service
- **Not Service Connected**: The VA did not find sufficient evidence of a link
- **Increased Evaluation**: Your rating for an existing condition was increased
- **Confirmed and Continued**: Your current rating was reviewed and remains the same

### What to Do Next

- Read your decision letter carefully, especially denied conditions
- Note the appeal deadline (1 year from decision date)
- If you disagree, explore your appeal options: Supplemental Claim, Higher-Level Review, or Board Appeal
- Use VetAssist's AI to help you understand your specific decision

---

*This is educational information only, not legal advice. Consult a VA-accredited representative for guidance specific to your situation.*"""
    },
    {
        'title': 'Common Conditions Veterans Claim',
        'slug': 'common-conditions-veterans-claim',
        'content_type': 'article',
        'difficulty_level': 'intermediate',
        'estimated_read_time': 8,
        'tags': json.dumps(['conditions', 'common', 'claims']),
        'summary': 'The most frequently claimed VA disability conditions — tinnitus, back injuries, knee conditions, PTSD, and more.',
        'content': """## Common Conditions Veterans Claim

Certain conditions are claimed by veterans far more frequently than others. Understanding these common claims can help you identify conditions you may have overlooked.

### Most Commonly Rated Disabilities

**1. Tinnitus (Ringing in the Ears)**
The #1 most claimed condition. Rated at 10% (maximum schedular rating). Often paired with hearing loss.

**2. Hearing Loss**
Rated from 0% to 100% based on audiometric testing. Bilateral hearing loss gets the bilateral factor bonus.

**3. PTSD and Mental Health Conditions**
Rated from 0% to 100%. Includes PTSD, depression, anxiety, and adjustment disorders.

**4. Back Conditions**
Lumbar strain, degenerative disc disease, and spinal stenosis. Rated on range of motion and incapacitating episodes.

**5. Knee Conditions**
Limitation of flexion, limitation of extension, and instability can all be rated separately for the same knee.

**6. Migraines**
Rated at 0%, 10%, 30%, or 50% based on frequency and severity of prostrating attacks.

**7. Sleep Apnea**
Rated at 0%, 30%, 50%, or 100%. Use of a CPAP machine is rated at 50%.

**8. Scars**
Painful, unstable, or disfiguring scars can be rated separately from the underlying condition.

**9. Radiculopathy**
Nerve pain radiating from the spine. Can be rated for each affected extremity.

**10. Flat Feet (Pes Planus)**
Rated from 0% to 50% based on severity and whether it's bilateral.

### Conditions You Might Be Missing

Many veterans focus on their primary conditions and miss related secondary conditions. Review the "Secondary Service Connection" article for common pairings.

### What to Do Next

- Review this list against your own conditions
- Consider whether any conditions might qualify as secondary to existing claims
- Use VetAssist's calculator to see how additional conditions affect your rating

---

*This is educational information only, not legal advice. Consult a VA-accredited representative for guidance specific to your situation.*"""
    },
    # === ADVANCED LEVEL ===
    {
        'title': 'Filing a Supplemental Claim',
        'slug': 'filing-supplemental-claim',
        'content_type': 'article',
        'difficulty_level': 'advanced',
        'estimated_read_time': 10,
        'tags': json.dumps(['appeals', 'supplemental', 'advanced']),
        'summary': 'When and how to file a Supplemental Claim — the most common appeal lane and its "new and relevant" evidence requirement.',
        'content': """## Filing a Supplemental Claim

If your VA claim was denied or you received a lower rating than expected, a Supplemental Claim is often the best path forward. It's the most commonly used appeal lane under the Appeals Modernization Act (AMA).

### Key Points

- A Supplemental Claim requires "new and relevant" evidence
- There is no time limit to file (but sooner is better for effective date)
- You can file a Supplemental Claim for any previously decided issue
- This is different from a Higher-Level Review or Board Appeal

### What Is "New and Relevant" Evidence?

**New**: Evidence that was not previously submitted to the VA
**Relevant**: Evidence that tends to prove or disprove an issue in your claim

Examples of new and relevant evidence:
- A new nexus letter from a different doctor
- Updated medical records showing worsening
- A buddy statement not previously submitted
- New research or medical literature supporting your claim

### When to Use a Supplemental Claim

- Your claim was denied for lack of evidence → get the missing evidence and refile
- You received a lower rating → get updated medical evidence showing severity
- You have a new medical opinion → submit it with a Supplemental Claim
- A previously denied secondary condition → get a stronger nexus opinion

### How to File

1. Complete VA Form 20-0995 (Decision Review Request: Supplemental Claim)
2. Identify the new and relevant evidence
3. Submit the form with your new evidence
4. The VA will review your claim with the new evidence included

### What to Do Next

- Identify what evidence was missing from your original claim
- Obtain the new evidence (nexus letter, medical records, buddy statements)
- File VA Form 20-0995 with your new evidence
- Use VetAssist's AI to help identify evidence gaps in your original claim

---

*This is educational information only, not legal advice. Consult a VA-accredited representative for guidance specific to your situation.*"""
    },
    {
        'title': 'Higher-Level Review vs Board Appeal',
        'slug': 'higher-level-review-vs-board-appeal',
        'content_type': 'article',
        'difficulty_level': 'advanced',
        'estimated_read_time': 12,
        'tags': json.dumps(['appeals', 'strategy', 'advanced']),
        'summary': 'Comparing the two other appeal lanes — when a Higher-Level Review makes sense vs when you should go to the Board.',
        'content': """## Higher-Level Review vs Board Appeal

Under the Appeals Modernization Act (AMA), you have three appeal options: Supplemental Claim, Higher-Level Review, and Board Appeal. Understanding when to use each is critical strategy.

### Key Points

- Higher-Level Review is a review by a more senior adjudicator — no new evidence allowed
- Board Appeal goes to a Veterans Law Judge — you can submit new evidence
- You can switch between lanes if one doesn't work
- The right choice depends on whether the error was in evidence evaluation or evidence itself

### Higher-Level Review (HLR)

**Filed on:** VA Form 20-0996
**Timeline:** ~4-6 months average
**New evidence:** NOT allowed

**Use when:**
- You believe the VA made a clear and obvious error in evaluating existing evidence
- The C&P examiner's report contradicts the rating decision
- The VA applied the wrong rating criteria
- You want a faster resolution without gathering new evidence

**What happens:** A senior adjudicator reviews the exact same evidence that was before the original rater. They can agree, disagree, or identify a "duty to assist" error.

### Board Appeal

**Filed on:** VA Form 10182
**Timeline:** ~1-2 years depending on docket
**New evidence:** Allowed (on Evidence Submission docket)

**Three docket options:**
1. **Direct Review**: Board reviews existing record only (fastest)
2. **Evidence Submission**: You can submit new evidence (no hearing)
3. **Hearing**: You testify before a Veterans Law Judge (slowest but most thorough)

**Use when:**
- You have significant new evidence to present
- The legal issues are complex
- You want to testify personally about your condition
- HLR was already tried and denied

### Decision Matrix

| Factor | HLR | Board Appeal |
|--------|-----|-------------|
| Speed | Faster (4-6 months) | Slower (1-2 years) |
| New evidence | No | Yes (Evidence/Hearing dockets) |
| Personal testimony | No | Yes (Hearing docket) |
| Error type | Evaluation error | Evidence gaps or legal complexity |

### What to Do Next

- Review your denial letter to understand the VA's reasoning
- Determine if the issue is an evaluation error (HLR) or missing evidence (Supplemental or Board)
- Consult with a VA-accredited attorney for complex cases
- Use VetAssist's AI to analyze your decision letter

---

*This is educational information only, not legal advice. Consult a VA-accredited representative for guidance specific to your situation.*"""
    },
    {
        'title': 'Total Disability Individual Unemployability (TDIU)',
        'slug': 'tdiu-total-disability-unemployability',
        'content_type': 'article',
        'difficulty_level': 'advanced',
        'estimated_read_time': 11,
        'tags': json.dumps(['tdiu', 'unemployability', 'advanced']),
        'summary': 'TDIU pays at the 100% rate even if your combined rating is lower — eligibility, evidence, and how to apply.',
        'content': """## Total Disability Based on Individual Unemployability (TDIU)

TDIU is one of the most valuable benefits available to veterans. It provides compensation at the 100% rate even if your combined disability rating is less than 100%.

### Key Points

- TDIU compensates you at the 100% rate ($3,737.85/month for a single veteran in 2025)
- You must be unable to maintain "substantially gainful employment" due to service-connected conditions
- There are two paths: schedular TDIU and extraschedular TDIU
- TDIU can be combined with other benefits like SMC (Special Monthly Compensation)

### Eligibility Requirements

**Schedular TDIU (38 CFR 4.16a):**
- One service-connected condition rated at 60% or higher, OR
- Two or more service-connected conditions with a combined rating of 70% or higher, with at least one condition rated at 40%

**Extraschedular TDIU (38 CFR 4.16b):**
- You don't meet the schedular thresholds above, BUT
- Your service-connected conditions still prevent substantially gainful employment
- Must be referred to the Director of Compensation Service for approval

### What Is "Substantially Gainful Employment"?

The VA defines this as employment that earns above the federal poverty threshold. Part-time work, marginal employment, or sheltered workshops generally don't count against you.

### Evidence for TDIU

1. **VA Form 21-8940** (Veteran's Application for Increased Compensation Based on Unemployability)
2. **VA Form 21-4192** (Request for Employment Information from current/former employers)
3. **Medical evidence** showing how your conditions prevent work
4. **Vocational expert opinion** (optional but powerful)
5. **Employment history** showing declining ability to work

### What to Do Next

- Check if you meet the schedular thresholds using VetAssist's calculator
- Document how your service-connected conditions affect your ability to work
- Gather employment records showing work difficulties or job loss
- Complete VA Form 21-8940

---

*This is educational information only, not legal advice. Consult a VA-accredited representative for guidance specific to your situation.*"""
    },
    {
        'title': 'The Bilateral Factor in VA Ratings',
        'slug': 'bilateral-factor-va-ratings',
        'content_type': 'article',
        'difficulty_level': 'advanced',
        'estimated_read_time': 6,
        'tags': json.dumps(['ratings', 'bilateral', 'calculator', 'advanced']),
        'summary': 'How the bilateral factor boosts your combined rating when you have conditions affecting paired extremities.',
        'content': """## The Bilateral Factor in VA Ratings

The bilateral factor is a special calculation the VA applies when you have disabilities affecting both paired extremities (both arms, both legs, or both sides of the body). It provides a small but meaningful boost to your combined rating.

### Key Points

- The bilateral factor adds approximately 10% to the combined value of bilateral disabilities
- It applies to arms, legs, and other paired body parts
- The boost is applied before combining with non-bilateral conditions
- It can push your rating into a higher rounded category

### How It Works

1. Identify all disabilities affecting paired extremities
2. Combine those bilateral disabilities using VA math
3. Add 10% of the combined bilateral value (this is the bilateral factor)
4. Then combine with remaining non-bilateral disabilities

### Example Calculation

**Conditions:**
- Left knee: 20%
- Right knee: 10%
- Back: 40%

**Without bilateral factor:**
Combined = 40% + 20% + 10% = 56% → rounds to 60%

**With bilateral factor:**
1. Bilateral knees combined: 100% - (80% × 90%) = 28%
2. Bilateral factor: 28% × 10% = 2.8% → bilateral total: 30.8%
3. Combine with back: 100% - (59.2% × 60%) = 64.48% → rounds to **60%**

In some cases the bilateral factor can push you from one rounding bracket to the next, which is where it really matters.

### When Does It Apply?

- Both knees, both hips, both shoulders, both ankles
- Radiculopathy affecting both lower or upper extremities
- Bilateral hearing loss
- Bilateral flat feet
- Any combination of conditions affecting both sides

### What to Do Next

- Review your conditions to see if the bilateral factor should apply
- Use VetAssist's calculator to see the impact of the bilateral factor on your rating
- If the VA didn't apply the bilateral factor correctly, it may be grounds for an appeal

---

*This is educational information only, not legal advice. Consult a VA-accredited representative for guidance specific to your situation.*"""
    },
    {
        'title': 'Presumptive Service Connection and the PACT Act',
        'slug': 'presumptive-service-connection-pact-act',
        'content_type': 'article',
        'difficulty_level': 'advanced',
        'estimated_read_time': 14,
        'tags': json.dumps(['presumptive', 'pact-act', 'agent-orange', 'advanced']),
        'summary': 'Agent Orange, burn pits, Gulf War illness — conditions the VA presumes are service-connected without needing a nexus.',
        'content': """## Presumptive Service Connection and the PACT Act

Presumptive service connection is a powerful provision that allows veterans to bypass the normal nexus requirement. If you served in specific locations or during specific time periods, certain conditions are automatically presumed to be service-connected.

### Key Points

- Presumptive conditions don't require a nexus letter
- You still need a current diagnosis and proof of qualifying service
- The PACT Act (2022) dramatically expanded presumptive conditions for burn pit and toxic exposure veterans
- Multiple presumptive categories exist for different eras and exposures

### The PACT Act (2022)

The Sergeant First Class Heath Robinson Honoring our Promise to Address Comprehensive Toxics (PACT) Act is the largest expansion of VA benefits in decades. Key provisions:

**Burn Pit / Airborne Hazards:**
- Covers veterans who served in Southwest Asia, Africa, and other locations after 9/11
- Presumptive conditions include: many cancers, respiratory conditions, constrictive bronchiolitis
- Concedes toxic exposure for all post-9/11 veterans who deployed to covered locations

**Agent Orange Expansion:**
- Added conditions: bladder cancer, hypertension, monoclonal gammopathy, early-onset peripheral neuropathy
- Extended coverage to veterans who served in Thailand, Guam, and other locations

### Presumptive Categories

**Vietnam Era (Agent Orange):**
- Service in Vietnam or offshore waters (1962-1975)
- Conditions: Type 2 diabetes, ischemic heart disease, Parkinson's disease, multiple cancers, and more

**Gulf War (Southwest Asia):**
- Service in Southwest Asia during Gulf War era
- Conditions: Chronic fatigue syndrome, fibromyalgia, functional gastrointestinal disorders, undiagnosed illnesses

**Post-9/11 (Burn Pits / Toxic Exposure):**
- Service in covered locations after September 11, 2001
- Conditions: Many cancers, respiratory conditions, constrictive bronchiolitis

**Radiation Exposure:**
- Veterans exposed to ionizing radiation during weapons testing or cleanup
- Conditions: Various cancers

### How to File a Presumptive Claim

1. Confirm your qualifying service dates and locations (DD-214, service records)
2. Get a current diagnosis of a presumptive condition
3. File VA Form 21-526EZ
4. No nexus letter needed — the VA presumes the connection

### What to Do Next

- Check if your service locations qualify under any presumptive category
- Register for the VA's toxic exposure screening
- File claims for any conditions on the presumptive lists
- Use VetAssist's AI to check if your conditions qualify for presumptive connection

---

*This is educational information only, not legal advice. Consult a VA-accredited representative for guidance specific to your situation.*"""
    },
]

def seed_content():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    inserted = 0
    skipped = 0

    for article in ARTICLES:
        # Check if slug already exists (idempotent)
        cur.execute("SELECT id FROM educational_content WHERE slug = %s", (article['slug'],))
        if cur.fetchone():
            print(f"  SKIP: {article['slug']} (already exists)")
            skipped += 1
            continue

        article_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        cur.execute("""
            INSERT INTO educational_content
                (id, title, slug, content_type, content, summary, difficulty_level,
                 estimated_read_time, tags, view_count, created_at, updated_at, is_published)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            article_id,
            article['title'],
            article['slug'],
            article['content_type'],
            article['content'],
            article['summary'],
            article['difficulty_level'],
            article['estimated_read_time'],
            article['tags'],  # Already JSON-serialized
            0,  # view_count
            now,  # created_at
            now,  # updated_at
            True  # is_published
        ))
        print(f"  OK: {article['slug']}")
        inserted += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"\nDone. Inserted: {inserted}, Skipped: {skipped}, Total articles: {len(ARTICLES)}")

if __name__ == '__main__':
    print("Seeding VetAssist educational content...")
    seed_content()
```

### Step 2: Run the seed script

```bash
cd /ganuda/vetassist/backend
./venv/bin/python scripts/seed_educational_content.py
```

### Step 3: Verify

```bash
# Check count
python3 -c "
import psycopg2
conn = psycopg2.connect(host='192.168.132.222', dbname='zammad_production', user='claude', password='jawaseatlasers2')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM educational_content WHERE is_published = true')
print('Published articles:', cur.fetchone()[0])
cur.execute('SELECT title, difficulty_level, tags FROM educational_content ORDER BY difficulty_level, title')
for row in cur.fetchall():
    print(f'  [{row[1]}] {row[0]} — tags: {row[2][:50]}')
conn.close()
"

# Check the API returns articles with tags as arrays
curl -s http://localhost:8001/api/v1/content?limit=3 | python3 -m json.tool | head -30
```

---

## Success Criteria

- 17 articles inserted into educational_content (18 total with the test row)
- All articles have: title, slug, content, summary, tags (JSON), difficulty_level, estimated_read_time, view_count=0, is_published=true
- Script is idempotent — running it twice doesn't create duplicates
- API returns articles with tags as JSON arrays (after VETASSIST-RESOURCES-FIX-001 backend fix)

---

## Content Coverage

| Level | Count | Topics |
|-------|-------|--------|
| Beginner | 6 | Claims overview, ratings math, claim types, evidence, timeline, VetAssist tutorial |
| Intermediate | 6 | PTSD, secondary conditions, C&P exam prep, buddy statements, decision letters, common conditions |
| Advanced | 5 | Supplemental claims, HLR vs Board appeal, TDIU, bilateral factor, presumptive/PACT Act |

---

## Security Notes

- No new credentials
- Content is educational only, with disclaimers on every article
- No PII in any article
- Script uses existing db credentials from standard config
