# JR Instruction: VetAssist Chat Quality Enhancement

## Metadata
```yaml
task_id: vetassist_chat_quality
priority: 2
assigned_to: VetAssist Jr.
target: backend
estimated_effort: medium
```

## Problem Statement

Chat answers are functional but not informative enough for veterans seeking help with VA claims. Current responses are generic and don't leverage:
1. Educational content database (empty or minimal content)
2. VA-specific CFR citations and regulations
3. Structured response format with actionable advice

## Objectives

1. **Seed educational content database** with real VA claims information
2. **Enhance council response quality** with better prompting
3. **Add citation formatting** with links to official VA sources
4. **Implement RAG retrieval** from educational content

## Tasks

### Task 1: Seed Educational Content Database

Create seed script `/ganuda/vetassist/backend/scripts/seed_educational_content.py`:

```python
#!/usr/bin/env python3
"""Seed VetAssist educational content database with VA claims information."""

import sys
sys.path.insert(0, '/ganuda/vetassist/backend')

import asyncio
from app.database import async_session
from app.models.educational_content import EducationalContent
from uuid import uuid4
from datetime import datetime

SEED_CONTENT = [
    {
        "title": "Understanding VA Disability Ratings",
        "slug": "understanding-va-disability-ratings",
        "content_type": "guide",
        "summary": "Learn how the VA calculates combined disability ratings using the whole person theory from 38 CFR 4.25.",
        "body": """# Understanding VA Disability Ratings

## The Whole Person Theory

The VA uses "whole person theory" from **38 CFR 4.25** to calculate combined disability ratings. This is NOT simple addition.

### How It Works

1. Start with your highest rating
2. Apply each subsequent rating to the remaining "able-bodied" percentage
3. Round to nearest 10%

### Example: 70% + 30% + 20%

| Step | Calculation | Result |
|------|-------------|--------|
| Start | 100% able | 100% |
| 70% rating | 100 × 0.70 = 70 | 30% remaining |
| 30% rating | 30 × 0.30 = 9 | 21% remaining |
| 20% rating | 21 × 0.20 = 4.2 | 16.8% remaining |
| Combined | 100 - 16.8 = 83.2% | **Rounds to 80%** |

### Key Citations
- **38 CFR 4.25**: Combined ratings table
- **38 CFR 4.26**: Bilateral factor (adds 10% to bilateral conditions before combining)
""",
        "difficulty_level": "beginner",
        "tags": ["ratings", "combined-rating", "38-cfr-4.25", "basics"],
        "estimated_read_time": 5,
    },
    {
        "title": "The Bilateral Factor Explained",
        "slug": "bilateral-factor-explained",
        "content_type": "guide",
        "summary": "How the bilateral factor (38 CFR 4.26) adds a 10% boost when you have conditions affecting both sides of your body.",
        "body": """# The Bilateral Factor (38 CFR 4.26)

## What is the Bilateral Factor?

When you have disabilities affecting **paired extremities** (both arms, both legs, both knees, etc.), the VA adds a 10% boost to those conditions before combining them with other ratings.

## How It Works

1. Combine all bilateral conditions together
2. Add 10% of that combined value
3. Then combine with non-bilateral conditions

### Example: Left Knee 30% + Right Knee 20%

| Step | Calculation | Result |
|------|-------------|--------|
| Combine knees | 100 - (30 × 70) = 44% | 44% combined |
| Bilateral factor | 44 × 0.10 = 4.4% | 4.4% boost |
| Total bilateral | 44 + 4.4 = 48.4% | 48.4% |

### What Qualifies

- Both arms/hands/shoulders
- Both legs/knees/feet/hips
- Both eyes
- Both ears (for hearing loss)

### What Does NOT Qualify

- One arm + one leg (not paired)
- Mental health conditions
- Internal organ conditions
""",
        "difficulty_level": "intermediate",
        "tags": ["bilateral-factor", "38-cfr-4.26", "paired-extremities", "ratings"],
        "estimated_read_time": 4,
    },
    {
        "title": "Special Monthly Compensation (SMC) Overview",
        "slug": "special-monthly-compensation-overview",
        "content_type": "guide",
        "summary": "Understanding SMC levels from K through S, and how they provide additional compensation beyond the 100% rate.",
        "body": """# Special Monthly Compensation (SMC)

## What is SMC?

Special Monthly Compensation is **additional payment beyond the 100% rate** for veterans with severe disabilities. It's authorized under **38 USC 1114**.

## SMC Levels

### SMC-K (Most Common)
- Loss of use of creative organ
- Loss of one hand/foot
- Blindness in one eye
- **Can be combined with any rating**
- Current rate: ~$131/month additional

### SMC-S (Housebound)
- 100% rating PLUS
- 60% or more in separate conditions
- OR permanently housebound
- Current rate: ~$441/month additional

### SMC-L through SMC-O
Higher levels for:
- Loss of multiple limbs
- Blindness
- Need for Aid & Attendance

### SMC-R and SMC-T
Highest levels for:
- Need for regular aid and attendance
- Traumatic brain injury requiring supervision

## Key Points

1. **SMC-K stacks** - you can get it for each qualifying loss
2. **SMC-S has two paths** - statutory or actual housebound
3. **SMC levels can combine** in complex ways

### Citation
- **38 USC 1114**: SMC authorization
- **38 CFR 3.350**: SMC rates and requirements
""",
        "difficulty_level": "advanced",
        "tags": ["smc", "special-monthly-compensation", "aid-attendance", "housebound"],
        "estimated_read_time": 7,
    },
    {
        "title": "Filing Your First VA Disability Claim",
        "slug": "filing-first-va-claim",
        "content_type": "guide",
        "summary": "Step-by-step guide to filing your initial VA disability claim, including required evidence and common mistakes to avoid.",
        "body": """# Filing Your First VA Disability Claim

## Before You Start

### Gather Your Evidence
1. **Service Treatment Records (STRs)** - Request from NPRC
2. **Current Medical Evidence** - Diagnosis and nexus
3. **Buddy Statements** - From fellow service members
4. **Personal Statement** - Your own account

## The Filing Process

### Step 1: Intent to File
File an **Intent to File (ITF)** immediately! This:
- Preserves your effective date for 1 year
- Gives you time to gather evidence
- Can mean thousands in back pay

### Step 2: Choose Your Filing Method
| Method | Pros | Cons |
|--------|------|------|
| eBenefits/VA.gov | Fast, trackable | Can be confusing |
| VSO assistance | Expert help, free | May have wait times |
| VA Form 21-526EZ | Paper backup | Slower processing |

### Step 3: Claim the Right Conditions
- **Claim everything** related to service
- Use proper terminology (match 38 CFR diagnostic codes)
- Include secondary conditions

### Step 4: C&P Exam
- Be honest about your worst days
- Bring documentation
- Don't minimize symptoms

## Common Mistakes

1. **Not filing Intent to File first**
2. **Missing the nexus** - connection to service
3. **Being too stoic** at C&P exams
4. **Not appealing denials** - many get reversed

## Timeline Expectations

- Initial claim: 3-6 months average
- Appeals: 6-18 months
- Higher Level Review: 125 days (median)
""",
        "difficulty_level": "beginner",
        "tags": ["filing", "first-claim", "intent-to-file", "c-and-p-exam", "evidence"],
        "estimated_read_time": 8,
    },
    {
        "title": "PTSD Claims: Evidence and Rating Criteria",
        "slug": "ptsd-claims-evidence-criteria",
        "content_type": "guide",
        "summary": "Detailed guide on filing PTSD claims including stressor verification, DBQ criteria, and rating levels from 0% to 100%.",
        "body": """# PTSD Claims: Evidence and Rating Criteria

## PTSD Claim Requirements

### The Three Elements
1. **Current diagnosis** of PTSD (DSM-5 criteria)
2. **In-service stressor** that caused it
3. **Nexus** - medical link between the two

## Stressor Verification

### Combat Veterans
- Combat Action Ribbon, Bronze Star, Purple Heart = **verified stressor**
- No additional proof needed

### Non-Combat Stressors
May need:
- Unit records
- Buddy statements
- Personal statement
- Military Sexual Trauma (MST) markers

### MST Claims
Special rules:
- Behavioral changes count as markers
- No formal report required
- Can use circumstantial evidence

## Rating Criteria (38 CFR 4.130)

### 0% - Diagnosis confirmed, no impairment
Symptoms controlled with medication

### 10% - Mild symptoms
Occupational and social impairment due to mild symptoms

### 30% - Occasional decrease in work efficiency
- Depressed mood
- Anxiety
- Chronic sleep impairment

### 50% - Reduced reliability and productivity
- Flattened affect
- Difficulty understanding complex commands
- Impaired judgment
- Disturbances of motivation and mood

### 70% - Deficiencies in most areas
- Suicidal ideation
- Obsessive rituals
- Illogical speech
- Near-continuous panic or depression
- Difficulty adapting to stress
- Inability to establish relationships

### 100% - Total occupational and social impairment
- Gross impairment in thought/communication
- Persistent danger to self/others
- Inability to perform basic self-care
- Disorientation
- Memory loss

## Key Citations
- **38 CFR 4.125**: PTSD diagnosis requirements
- **38 CFR 4.130**: Mental health rating schedule
- **38 CFR 3.304(f)**: Stressor verification rules
""",
        "difficulty_level": "intermediate",
        "tags": ["ptsd", "mental-health", "stressor", "mst", "rating-criteria"],
        "estimated_read_time": 10,
    },
]

async def seed_content():
    async with async_session() as session:
        for item in SEED_CONTENT:
            content = EducationalContent(
                id=uuid4(),
                title=item["title"],
                slug=item["slug"],
                content_type=item["content_type"],
                summary=item["summary"],
                body=item["body"],
                difficulty_level=item["difficulty_level"],
                tags=item["tags"],
                estimated_read_time=item["estimated_read_time"],
                author_id=None,
                is_published=True,
                view_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(content)
        await session.commit()
        print(f"Seeded {len(SEED_CONTENT)} educational articles")

if __name__ == "__main__":
    asyncio.run(seed_content())
```

### Task 2: Enhance Council Response Prompting

Update `/ganuda/vetassist/backend/app/services/chat_service.py` council prompt:

```python
COUNCIL_SYSTEM_PROMPT = """You are a specialist in the VetAssist AI Council helping veterans understand VA disability claims.

RESPONSE FORMAT:
1. **Direct Answer** - Answer the question clearly first
2. **Explanation** - Provide context and reasoning
3. **Relevant Citations** - Include CFR/USC references
4. **Action Items** - Give concrete next steps when applicable
5. **Disclaimer** - Brief reminder this is educational only

CITATION GUIDELINES:
- Always cite 38 CFR sections when discussing ratings or procedures
- Reference 38 USC for statutory authority
- Link to va.gov when referencing forms or processes

TONE:
- Empathetic and supportive
- Clear and direct, not overly formal
- Acknowledge the stress of the claims process
- Never dismiss or minimize concerns

KNOWLEDGE BASE:
{educational_context}
"""
```

### Task 3: Implement RAG Retrieval

Add content retrieval to chat endpoint in `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py`:

```python
async def get_relevant_content(query: str, limit: int = 3) -> str:
    """Retrieve relevant educational content for RAG."""
    async with async_session() as session:
        # Simple keyword search - can be enhanced with embeddings later
        results = await session.execute(
            select(EducationalContent)
            .where(EducationalContent.is_published == True)
            .limit(limit)
        )
        content = results.scalars().all()

        if not content:
            return ""

        context = "RELEVANT EDUCATIONAL CONTENT:\n\n"
        for item in content:
            context += f"## {item.title}\n{item.summary}\n\n"
        return context
```

## Verification

1. Run seed script: `python /ganuda/vetassist/backend/scripts/seed_educational_content.py`
2. Verify content: Check `/resources` page shows new articles
3. Test chat: Ask "How do VA disability ratings work?" - should get detailed response with citations
4. Check citations: Response should include 38 CFR references

## Success Criteria

- [ ] Educational content database has 5+ quality articles
- [ ] Chat responses include CFR citations
- [ ] Responses follow structured format
- [ ] Users can click through to educational resources

---

*Cherokee AI Federation - For the Seven Generations*
