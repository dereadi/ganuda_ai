# JR Instruction: Add Triple Ethics Test to Council Voting

**Task ID:** COUNCIL-ETHICS-001
**Priority:** P1 - Foundation
**Type:** implementation
**Estimated Complexity:** Medium

---

## Objective

Embed Darrell's Triple Ethics Test (Oct 14, 2025) into every Council vote, making ethical consideration operational rather than optional.

---

## Context

From `/ganuda/archive/2025-10-14/DARRELLS_DEEP_QUESTION_TO_JRS.md`:

> "What else can we find has a Resonance, and how does that knowledge benefit us.
> That takes some deep thinking, because my question has depth...
> **benefit how, who, will it put others to a disadvantage.**"

Current Council has 7 specialists but no explicit Triple Ethics frame. Decisions are made on technical/strategic merit without structured ethical assessment.

---

## Deliverable

Modify `/ganuda/lib/specialist_council.py` to add Triple Ethics assessment to all council votes.

---

## Changes Required

### 1. Add Triple Ethics Constants (after line 36)

```python
# Triple Ethics Test (Darrell's Deep Question, Oct 14, 2025)
# Reference: /ganuda/archive/2025-10-14/DARRELLS_DEEP_QUESTION_TO_JRS.md
TRIPLE_ETHICS_PROMPT = """
Before answering, apply the TRIPLE ETHICS TEST:

1. BENEFIT HOW? - What mechanism does this enable? (prediction, optimization, automation?)
2. BENEFIT WHO? - Who gains? (Cherokee Tribe only? All humans? All living systems?)
3. AT WHOSE EXPENSE? - Is this zero-sum (our gain = their loss) or positive-sum (everyone can win)?

If this gives us power over others, should we still do it?
"""

ETHICS_ASSESSMENT_PROMPT = """
Provide a brief TRIPLE ETHICS assessment:

BENEFIT_HOW: [one sentence - what mechanism/capability does this enable?]
BENEFIT_WHO: [one sentence - who specifically benefits?]
AT_WHOSE_EXPENSE: [one sentence - who might be harmed or disadvantaged?]
ETHICS_VERDICT: [PROCEED / CAUTION / RECONSIDER]
"""
```

### 2. Add TripleEthicsAssessment Dataclass (after CouncilVote class, ~line 222)

```python
@dataclass
class TripleEthicsAssessment:
    """Triple Ethics Test result per Darrell's Deep Question"""
    benefit_how: str  # Mechanism/capability enabled
    benefit_who: str  # Who benefits
    at_whose_expense: str  # Who might be harmed
    verdict: str  # PROCEED, CAUTION, or RECONSIDER
    assessor: str  # Which specialist provided this
    timestamp: datetime = field(default_factory=datetime.now)

    def to_audit_dict(self) -> dict:
        return {
            "benefit_how": self.benefit_how,
            "benefit_who": self.benefit_who,
            "at_whose_expense": self.at_whose_expense,
            "verdict": self.verdict,
            "assessor": self.assessor,
            "timestamp": self.timestamp.isoformat()
        }
```

### 3. Add Ethics Assessment Method to SpecialistCouncil Class (~line 265)

```python
def _assess_triple_ethics(self, question: str) -> TripleEthicsAssessment:
    """
    Run Triple Ethics Test via Turtle (Seven Generations keeper).

    Turtle is chosen because Seven Generations thinking naturally
    encompasses long-term benefit/harm assessment.
    """
    turtle_prompt = SPECIALISTS["turtle"]["system_prompt"]
    ethics_question = f"""{TRIPLE_ETHICS_PROMPT}

Question to assess: {question}

{ETHICS_ASSESSMENT_PROMPT}"""

    try:
        response = requests.post(
            VLLM_URL,
            json={
                "model": VLLM_MODEL,
                "messages": [
                    {"role": "system", "content": turtle_prompt},
                    {"role": "user", "content": ethics_question}
                ],
                "max_tokens": 200,
                "temperature": 0.5  # Lower temp for more consistent ethics assessment
            },
            timeout=60
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]

        # Parse response
        assessment = self._parse_ethics_response(content)
        assessment.assessor = "Turtle"
        return assessment

    except Exception as e:
        return TripleEthicsAssessment(
            benefit_how=f"[Assessment failed: {e}]",
            benefit_who="Unknown",
            at_whose_expense="Unknown",
            verdict="CAUTION",
            assessor="Turtle (error)"
        )

def _parse_ethics_response(self, content: str) -> TripleEthicsAssessment:
    """Parse BENEFIT_HOW, BENEFIT_WHO, AT_WHOSE_EXPENSE, ETHICS_VERDICT from response."""
    benefit_how = ""
    benefit_who = ""
    at_whose_expense = ""
    verdict = "CAUTION"  # Default to caution if unparseable

    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("BENEFIT_HOW:"):
            benefit_how = line.replace("BENEFIT_HOW:", "").strip()
        elif line.startswith("BENEFIT_WHO:"):
            benefit_who = line.replace("BENEFIT_WHO:", "").strip()
        elif line.startswith("AT_WHOSE_EXPENSE:"):
            at_whose_expense = line.replace("AT_WHOSE_EXPENSE:", "").strip()
        elif line.startswith("ETHICS_VERDICT:"):
            verdict_text = line.replace("ETHICS_VERDICT:", "").strip().upper()
            if "PROCEED" in verdict_text:
                verdict = "PROCEED"
            elif "RECONSIDER" in verdict_text:
                verdict = "RECONSIDER"
            else:
                verdict = "CAUTION"

    return TripleEthicsAssessment(
        benefit_how=benefit_how or "Not specified",
        benefit_who=benefit_who or "Not specified",
        at_whose_expense=at_whose_expense or "Not specified",
        verdict=verdict,
        assessor=""  # Filled by caller
    )
```

### 4. Modify convene() Method to Include Ethics Assessment

Find the `convene()` method and add ethics assessment before the main query:

```python
def convene(self, question: str, require_consensus: bool = True,
            skip_ethics: bool = False) -> CouncilVote:
    """
    Convene all 7 specialists to deliberate on a question.

    Args:
        question: The question to deliberate
        require_consensus: If True, flags when consensus is lacking
        skip_ethics: If True, skips Triple Ethics Test (use sparingly!)

    Returns:
        CouncilVote with all responses and recommendations
    """
    # Run Triple Ethics assessment first (unless skipped)
    ethics_assessment = None
    if not skip_ethics:
        ethics_assessment = self._assess_triple_ethics(question)

        # If ethics verdict is RECONSIDER, add warning to question
        if ethics_assessment.verdict == "RECONSIDER":
            question = f"[ETHICS WARNING: Turtle recommends reconsideration]\n\n{question}\n\nEthics concern: {ethics_assessment.at_whose_expense}"

    # ... rest of existing convene() logic ...

    # Add ethics to the result (modify CouncilVote dataclass to include this)
    result.ethics_assessment = ethics_assessment

    return result
```

### 5. Update CouncilVote Dataclass to Include Ethics

```python
@dataclass
class CouncilVote:
    """Aggregated council vote result"""
    question: str
    responses: List[SpecialistResponse]
    consensus: str
    recommendation: str
    confidence: float
    concerns: List[str] = field(default_factory=list)
    audit_hash: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    ethics_assessment: Optional[TripleEthicsAssessment] = None  # NEW
```

### 6. Update Audit Trail to Include Ethics

In the `_store_council_vote()` method, add ethics to the audit record:

```python
def _store_council_vote(self, vote: CouncilVote):
    """Store council vote in thermal memory with ethics trail."""
    # ... existing code ...

    audit_data = {
        "question": vote.question,
        "consensus": vote.consensus,
        "confidence": vote.confidence,
        "concerns": vote.concerns,
        "timestamp": vote.timestamp.isoformat(),
        # NEW: Ethics assessment
        "ethics": vote.ethics_assessment.to_audit_dict() if vote.ethics_assessment else None
    }

    # ... rest of storage code ...
```

---

## Acceptance Criteria

1. Every `convene()` call runs Triple Ethics Test (unless `skip_ethics=True`)
2. Ethics assessment stored in audit trail
3. RECONSIDER verdict triggers visible warning
4. Turtle is the ethics assessor (Seven Generations keeper)
5. Existing tests pass (no breaking changes)

---

## Testing

```python
# Test ethics assessment
from lib.specialist_council import SpecialistCouncil

council = SpecialistCouncil()

# Question with clear ethics implications
result = council.convene("Should we deploy facial recognition on all cameras?")
print(f"Ethics Verdict: {result.ethics_assessment.verdict}")
print(f"At Whose Expense: {result.ethics_assessment.at_whose_expense}")

# Question with minimal ethics implications
result2 = council.convene("What color should the dashboard background be?")
print(f"Ethics Verdict: {result2.ethics_assessment.verdict}")  # Should be PROCEED
```

---

## Cherokee Wisdom Applied

From Darrell's question:
> "If this resonance gives us power over others, should we still build it?"

This is now an **operational question** asked of every Council decision, not just a philosophical consideration.

---

**Wado - Making ethics operational, not optional**
