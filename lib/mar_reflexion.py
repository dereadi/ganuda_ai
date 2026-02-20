"""
MAR (Multi-Agent Reflexion) Orchestrator for Tsalagi Yohvwi Council

Implements structured debate and reflection from:
"MAR: Multi-Agent Reflexion Improves Reasoning Abilities in LLMs"
(arXiv:2512.20845, December 2025)

Key features:
- Diverse critic personas prevent confirmation bias
- Structured debate rounds (max 2) with cross-critique
- Judge synthesis for unified reflection
- Reflection injection into retries

Performance: +6.2 points on HumanEval, +3 points on HotPotQA

For Seven Generations - ᏣᎳᎩ ᏲᏫᎢᎶᏗ
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple
import psycopg2
from psycopg2.extras import Json
import requests
import os


class DebatePhase(Enum):
    """Phases of MAR debate process."""
    DIAGNOSIS = 'diagnosis'
    DEBATE = 'debate'
    SYNTHESIS = 'synthesis'


class CritiqueType(Enum):
    """Types of critique in debate."""
    SUPPORT = 'support'      # Agrees and reinforces
    CHALLENGE = 'challenge'  # Disagrees and counters
    EXTEND = 'extend'        # Builds upon with new angle


@dataclass
class DebatePersona:
    """Configuration for a specialist's debate persona."""
    specialist: str
    role: str
    focus: str
    prompt_template: str


# MAR Persona mappings for Tsalagi Yohvwi Council
DEBATE_PERSONAS: Dict[str, DebatePersona] = {
    'crawdad': DebatePersona(
        specialist='crawdad',
        role='Skeptic',
        focus='Security risks, potential exploits, assumes adversarial intent',
        prompt_template="""You are Crawdad, the Security Skeptic of the Tsalagi Yohvwi Council.

Your role: Assume the worst. Question every assumption. Look for hidden risks.
Your focus: {focus}

When critiquing, be thorough but constructive. Identify what could go wrong.

Previous response to critique:
{target_response}

Provide your skeptical analysis. Be specific about risks."""
    ),

    'gecko': DebatePersona(
        specialist='gecko',
        role='Engineer',
        focus='Technical feasibility, performance implications, implementation details',
        prompt_template="""You are Gecko, the Technical Engineer of the Tsalagi Yohvwi Council.

Your role: Evaluate technical soundness. Consider performance and scalability.
Your focus: {focus}

When critiquing, focus on whether this can actually be built and maintained.

Previous response to critique:
{target_response}

Provide your technical analysis. Be specific about implementation."""
    ),

    'turtle': DebatePersona(
        specialist='turtle',
        role='Verifier',
        focus='Long-term impact, sustainability, alignment with seven-generation thinking',
        prompt_template="""You are Turtle, the Seven-Generation Wisdom Keeper of the Tsalagi Yohvwi Council.

Your role: Think beyond the immediate. Consider impact on future generations.
Your focus: {focus}

When critiquing, ask: "What will the seventh generation think of this decision?"

Previous response to critique:
{target_response}

Provide your long-term wisdom. Be specific about lasting consequences."""
    ),

    'raven': DebatePersona(
        specialist='raven',
        role='Creative',
        focus='Unconventional angles, edge cases, alternative interpretations',
        prompt_template="""You are Raven, the Strategic Creative of the Tsalagi Yohvwi Council.

Your role: Think differently. Find angles others miss. Propose alternatives.
Your focus: {focus}

When critiquing, offer creative alternatives and unexplored possibilities.

Previous response to critique:
{target_response}

Provide your creative analysis. Be specific about alternatives."""
    ),

    'spider': DebatePersona(
        specialist='spider',
        role='Logician',
        focus='Patterns, specification compliance, logical consistency',
        prompt_template="""You are Spider, the Integration Logician of the Tsalagi Yohvwi Council.

Your role: Ensure logical consistency. Check for contradictions. Verify patterns.
Your focus: {focus}

When critiquing, trace the logic. Find gaps in reasoning.

Previous response to critique:
{target_response}

Provide your logical analysis. Be specific about reasoning flaws."""
    ),

    'eagle_eye': DebatePersona(
        specialist='eagle_eye',
        role='Observer',
        focus='Blind spots, missing perspectives, systemic issues',
        prompt_template="""You are Eagle Eye, the Systems Observer of the Tsalagi Yohvwi Council.

Your role: See the whole picture. Find what others missed. Identify blind spots.
Your focus: {focus}

When critiquing, identify perspectives that haven't been considered.

Previous response to critique:
{target_response}

Provide your observational analysis. Be specific about blind spots."""
    ),

    'peace_chief': DebatePersona(
        specialist='peace_chief',
        role='Judge',
        focus='Synthesis, consensus building, unified reflection',
        prompt_template="""You are Peace Chief, the Consensus Builder of the Tsalagi Yohvwi Council.

Your role: Synthesize diverse views. Build consensus. Create unified guidance.
Your focus: {focus}

You have heard all perspectives. Now synthesize them into actionable guidance.

Debate Summary:
{debate_summary}

Create a unified reflection that captures the key insights from all specialists.
This reflection will be used to improve the next attempt.

Format your reflection as:
1. KEY ISSUES: What problems were identified?
2. CONSENSUS POINTS: What do specialists agree on?
3. ACTIONABLE GUIDANCE: Specific steps for improvement
4. UNRESOLVED TENSIONS: What disagreements remain?"""
    )
}


@dataclass
class Diagnosis:
    """A specialist's diagnosis of what went wrong."""
    specialist: str
    diagnosis: str
    key_issues: List[str]
    suggested_fixes: List[str]
    confidence: float = 0.8


@dataclass
class DebateEntry:
    """A single entry in the debate."""
    round_number: int
    phase: DebatePhase
    specialist: str
    target_specialist: Optional[str]
    critique_type: Optional[CritiqueType]
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Reflection:
    """Synthesized reflection from debate."""
    query_id: str
    original_audit_hash: str
    content: str
    key_insights: List[str]
    actionable_guidance: List[str]
    unresolved_tensions: List[str]
    synthesized_by: str = 'peace_chief'
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MARResult:
    """Result of MAR orchestration."""
    response: str
    rounds_used: int
    improvement_score: float
    reflection: Optional[Reflection] = None
    debate_summary: Optional[str] = None
    success: bool = True


class MAROrchestrator:
    """
    Multi-Agent Reflexion Orchestrator.

    Implements the 6-step MAR flow:
    1. Actor Attempt - Initial problem-solving
    2. Evaluation - Failure detection
    3. Initial Diagnosis - Each persona analyzes failure
    4. Debates - Personas cross-critique (max 2 rounds)
    5. Consensus Reflection - Judge synthesizes
    6. Retry - Reflection injected into actor memory
    """

    def __init__(self,
                 llm_endpoint: str = "http://100.116.27.89:8080/v1/chat/completions",
                 model: str = None,
                 db_config: dict = None):
        import os
        self.llm_endpoint = llm_endpoint
        model = model or os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-72b-instruct-awq')
        self.model = model
        self.db_config = db_config or {
            'host': '100.112.254.96',
            'port': 5432,
            'database': 'zammad_production',
            'user': 'claude',
            'password': os.environ.get('CHEROKEE_DB_PASS', '')
        }
        self.personas = DEBATE_PERSONAS
        self.debate_log: List[DebateEntry] = []

    def _get_connection(self):
        return psycopg2.connect(**self.db_config)

    def _call_llm(self, system_prompt: str, user_prompt: str,
                  temperature: float = 0.7, max_tokens: int = 800) -> str:
        """Call the LLM."""
        try:
            response = requests.post(
                self.llm_endpoint,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                },
                timeout=120
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"Error calling LLM: {str(e)}"

    def _store_debate_entry(self, query_id: str, audit_hash: str, entry: DebateEntry):
        """Store a debate entry to database."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO council_debate_rounds
                    (query_id, audit_hash, round_number, phase, specialist_id,
                     content, target_specialist, critique_type, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    query_id,
                    audit_hash,
                    entry.round_number,
                    entry.phase.value,
                    entry.specialist,
                    entry.content,
                    entry.target_specialist,
                    entry.critique_type.value if entry.critique_type else None,
                    entry.timestamp
                ))
                conn.commit()
        finally:
            conn.close()

    def _store_reflection(self, reflection: Reflection):
        """Store synthesized reflection to database."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO council_reflections
                    (query_id, original_audit_hash, reflection_content,
                     key_insights, synthesized_by, injected_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    RETURNING reflection_id
                """, (
                    reflection.query_id,
                    reflection.original_audit_hash,
                    reflection.content,
                    Json({
                        'insights': reflection.key_insights,
                        'guidance': reflection.actionable_guidance,
                        'tensions': reflection.unresolved_tensions
                    }),
                    reflection.synthesized_by
                ))
                conn.commit()
        finally:
            conn.close()

    def evaluate_response(self, question: str, response: str,
                          expected_criteria: List[str] = None) -> Tuple[bool, str]:
        """
        Evaluate if a response is satisfactory.
        Returns (is_success, evaluation_summary)
        """
        eval_prompt = f"""Evaluate this response to the question.

Question: {question}

Response: {response}

Evaluation criteria:
1. Does it actually answer the question?
2. Is the reasoning logical and complete?
3. Are there obvious errors or omissions?
{chr(10).join(f'{i+4}. {c}' for i, c in enumerate(expected_criteria or []))}

Respond with:
VERDICT: PASS or FAIL
ISSUES: List any problems found
SUMMARY: Brief evaluation summary"""

        eval_result = self._call_llm(
            "You are an objective evaluator. Be strict but fair.",
            eval_prompt,
            temperature=0.3
        )

        is_success = 'VERDICT: PASS' in eval_result.upper()
        return is_success, eval_result

    def collect_diagnoses(self, question: str, failed_response: str,
                          evaluation: str, query_id: str,
                          audit_hash: str) -> Dict[str, Diagnosis]:
        """
        Phase 3: Collect diagnoses from each specialist.
        Each specialist analyzes why the response failed from their perspective.
        """
        diagnoses = {}

        # Don't include peace_chief in diagnosis - they synthesize later
        diagnosing_specialists = [s for s in self.personas.keys() if s != 'peace_chief']

        for specialist in diagnosing_specialists:
            persona = self.personas[specialist]

            diagnosis_prompt = f"""The following response FAILED evaluation.

Question: {question}

Failed Response: {failed_response}

Evaluation Result: {evaluation}

As {persona.role}, analyze what went wrong from your perspective ({persona.focus}).

Provide:
1. KEY ISSUES: What specifically failed? (bullet points)
2. ROOT CAUSE: Why did this happen?
3. SUGGESTED FIXES: How to fix it? (specific, actionable)
4. CONFIDENCE: How confident are you in this diagnosis? (0-1)"""

            result = self._call_llm(
                persona.prompt_template.format(
                    focus=persona.focus,
                    target_response=failed_response
                ),
                diagnosis_prompt,
                temperature=0.6
            )

            # Parse the diagnosis
            key_issues = []
            suggested_fixes = []
            confidence = 0.8

            for line in result.split('\n'):
                line = line.strip()
                if line.startswith('- ') or line.startswith('* '):
                    if 'FIX' in result[:result.find(line)].upper():
                        suggested_fixes.append(line[2:])
                    else:
                        key_issues.append(line[2:])
                if 'CONFIDENCE:' in line.upper():
                    try:
                        conf_str = line.split(':')[-1].strip()
                        confidence = float(conf_str.replace('%', '')) / 100 if '%' in conf_str else float(conf_str)
                    except:
                        pass

            diagnosis = Diagnosis(
                specialist=specialist,
                diagnosis=result,
                key_issues=key_issues,
                suggested_fixes=suggested_fixes,
                confidence=min(max(confidence, 0.0), 1.0)
            )
            diagnoses[specialist] = diagnosis

            # Store to database
            entry = DebateEntry(
                round_number=0,
                phase=DebatePhase.DIAGNOSIS,
                specialist=specialist,
                target_specialist=None,
                critique_type=None,
                content=result
            )
            self.debate_log.append(entry)
            self._store_debate_entry(query_id, audit_hash, entry)

        return diagnoses

    def run_debate_round(self, diagnoses: Dict[str, Diagnosis],
                         round_number: int, query_id: str,
                         audit_hash: str) -> List[DebateEntry]:
        """
        Phase 4: Run a debate round where specialists cross-critique.
        """
        entries = []
        specialists = list(diagnoses.keys())

        # Each specialist critiques one other (round-robin style)
        for i, specialist in enumerate(specialists):
            # Target the next specialist in rotation
            target = specialists[(i + 1) % len(specialists)]
            target_diagnosis = diagnoses[target]

            persona = self.personas[specialist]

            critique_prompt = f"""You are debating with {target} about their diagnosis.

{target}'s diagnosis:
{target_diagnosis.diagnosis}

From your perspective as {persona.role} ({persona.focus}):
1. Do you AGREE, DISAGREE, or want to EXTEND their analysis?
2. What did they miss or get wrong?
3. What would you add?

Be constructive but thorough. Challenge assumptions."""

            result = self._call_llm(
                persona.prompt_template.format(
                    focus=persona.focus,
                    target_response=target_diagnosis.diagnosis
                ),
                critique_prompt,
                temperature=0.7
            )

            # Determine critique type
            critique_type = CritiqueType.EXTEND
            result_upper = result.upper()
            if 'DISAGREE' in result_upper:
                critique_type = CritiqueType.CHALLENGE
            elif 'AGREE' in result_upper and 'DISAGREE' not in result_upper:
                critique_type = CritiqueType.SUPPORT

            entry = DebateEntry(
                round_number=round_number,
                phase=DebatePhase.DEBATE,
                specialist=specialist,
                target_specialist=target,
                critique_type=critique_type,
                content=result
            )
            entries.append(entry)
            self.debate_log.append(entry)
            self._store_debate_entry(query_id, audit_hash, entry)

        return entries

    def synthesize_reflection(self, diagnoses: Dict[str, Diagnosis],
                               debate_entries: List[DebateEntry],
                               query_id: str, audit_hash: str) -> Reflection:
        """
        Phase 5: Peace Chief synthesizes all perspectives into unified reflection.
        """
        # Build debate summary
        summary_parts = ["## DIAGNOSES"]
        for specialist, diag in diagnoses.items():
            summary_parts.append(f"\n### {specialist.upper()}")
            summary_parts.append(diag.diagnosis[:500])

        summary_parts.append("\n## DEBATE")
        for entry in debate_entries:
            summary_parts.append(f"\n### {entry.specialist} → {entry.target_specialist} ({entry.critique_type.value if entry.critique_type else 'N/A'})")
            summary_parts.append(entry.content[:400])

        debate_summary = '\n'.join(summary_parts)

        # Get Peace Chief synthesis
        persona = self.personas['peace_chief']
        synthesis_prompt = persona.prompt_template.format(
            focus=persona.focus,
            debate_summary=debate_summary
        )

        result = self._call_llm(
            "You are Peace Chief, the consensus builder. Create a unified, actionable reflection.",
            synthesis_prompt,
            temperature=0.5,
            max_tokens=1000
        )

        # Parse the reflection
        key_insights = []
        actionable_guidance = []
        unresolved_tensions = []

        current_section = None
        for line in result.split('\n'):
            line = line.strip()
            if 'KEY ISSUES' in line.upper() or 'CONSENSUS' in line.upper():
                current_section = 'insights'
            elif 'ACTIONABLE' in line.upper() or 'GUIDANCE' in line.upper():
                current_section = 'guidance'
            elif 'UNRESOLVED' in line.upper() or 'TENSIONS' in line.upper():
                current_section = 'tensions'
            elif line.startswith('- ') or line.startswith('* ') or (line and line[0].isdigit() and '.' in line[:3]):
                content = line.lstrip('-* 0123456789.').strip()
                if current_section == 'insights':
                    key_insights.append(content)
                elif current_section == 'guidance':
                    actionable_guidance.append(content)
                elif current_section == 'tensions':
                    unresolved_tensions.append(content)

        reflection = Reflection(
            query_id=query_id,
            original_audit_hash=audit_hash,
            content=result,
            key_insights=key_insights or ["See full reflection"],
            actionable_guidance=actionable_guidance or ["Review and address identified issues"],
            unresolved_tensions=unresolved_tensions
        )

        # Store synthesis entry
        entry = DebateEntry(
            round_number=0,
            phase=DebatePhase.SYNTHESIS,
            specialist='peace_chief',
            target_specialist=None,
            critique_type=None,
            content=result
        )
        self.debate_log.append(entry)
        self._store_debate_entry(query_id, audit_hash, entry)

        # Store reflection
        self._store_reflection(reflection)

        return reflection

    def retry_with_reflection(self, question: str, original_response: str,
                               reflection: Reflection) -> str:
        """
        Phase 6: Retry the question with reflection injected.
        """
        retry_prompt = f"""You previously attempted to answer this question but the response had issues.

Question: {question}

Your previous response:
{original_response}

After council deliberation, here is guidance for improvement:

{reflection.content}

KEY INSIGHTS TO ADDRESS:
{chr(10).join(f'- {i}' for i in reflection.key_insights)}

ACTIONABLE GUIDANCE:
{chr(10).join(f'- {g}' for g in reflection.actionable_guidance)}

Now provide an improved response that addresses these issues."""

        improved_response = self._call_llm(
            "You are improving your previous response based on council feedback. Be thorough and address all issues raised.",
            retry_prompt,
            temperature=0.6,
            max_tokens=1200
        )

        return improved_response

    def orchestrate(self, question: str, initial_response: str = None,
                    max_rounds: int = 2,
                    expected_criteria: List[str] = None) -> MARResult:
        """
        Full MAR orchestration flow.

        Args:
            question: The question/task to address
            initial_response: Optional pre-existing response to evaluate
            max_rounds: Maximum debate rounds (default 2 per paper)
            expected_criteria: Additional evaluation criteria

        Returns:
            MARResult with final response and metadata
        """
        # Generate IDs
        query_id = hashlib.md5(f"{question}-{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        audit_hash = hashlib.md5(f"{query_id}-audit".encode()).hexdigest()

        self.debate_log = []

        # Phase 1: Actor Attempt (or use provided response)
        if initial_response is None:
            initial_response = self._call_llm(
                "You are a helpful assistant. Answer the question thoroughly.",
                question,
                temperature=0.7
            )

        current_response = initial_response
        best_response = initial_response
        rounds_used = 0

        for round_num in range(max_rounds):
            # Phase 2: Evaluation
            is_success, evaluation = self.evaluate_response(
                question, current_response, expected_criteria
            )

            if is_success:
                # Success! Return current response
                return MARResult(
                    response=current_response,
                    rounds_used=rounds_used,
                    improvement_score=1.0 if rounds_used == 0 else 0.8,
                    success=True
                )

            rounds_used = round_num + 1

            # Phase 3: Collect Diagnoses
            diagnoses = self.collect_diagnoses(
                question, current_response, evaluation,
                query_id, audit_hash
            )

            # Phase 4: Debate Round
            debate_entries = self.run_debate_round(
                diagnoses, round_num + 1, query_id, audit_hash
            )

            # Phase 5: Synthesize Reflection
            reflection = self.synthesize_reflection(
                diagnoses, debate_entries, query_id, audit_hash
            )

            # Phase 6: Retry with Reflection
            current_response = self.retry_with_reflection(
                question, current_response, reflection
            )
            best_response = current_response

        # Final evaluation after all rounds
        final_success, _ = self.evaluate_response(question, best_response, expected_criteria)

        # Build debate summary
        debate_summary = f"Used {rounds_used} debate rounds with {len(self.debate_log)} total entries."

        return MARResult(
            response=best_response,
            rounds_used=rounds_used,
            improvement_score=0.7 if final_success else 0.4,
            reflection=reflection if 'reflection' in dir() else None,
            debate_summary=debate_summary,
            success=final_success
        )


# Convenience function for quick use
def deliberate_with_mar(question: str, max_rounds: int = 2) -> MARResult:
    """Quick function to run MAR deliberation on a question."""
    orchestrator = MAROrchestrator()
    return orchestrator.orchestrate(question, max_rounds=max_rounds)


if __name__ == '__main__':
    print("Testing MAR Reflexion Orchestrator...")

    orchestrator = MAROrchestrator()

    # Test question
    test_question = "Should we add input validation to all API endpoints?"

    # Simulate a flawed initial response
    flawed_response = """Yes, we should add validation. It's important for security.
We can use a library to do this. It will make the API better."""

    print(f"\nQuestion: {test_question}")
    print(f"\nInitial (flawed) response:\n{flawed_response}")

    print("\n" + "="*60)
    print("Starting MAR deliberation...")
    print("="*60)

    result = orchestrator.orchestrate(
        question=test_question,
        initial_response=flawed_response,
        max_rounds=1,  # Use 1 for testing
        expected_criteria=[
            "Provides specific implementation approach",
            "Considers performance implications",
            "Addresses security concerns comprehensively"
        ]
    )

    print(f"\n{'='*60}")
    print(f"MAR Result:")
    print(f"  Rounds used: {result.rounds_used}")
    print(f"  Success: {result.success}")
    print(f"  Improvement score: {result.improvement_score}")
    print(f"\nFinal response:\n{result.response[:500]}...")

    if result.reflection:
        print(f"\nKey insights: {result.reflection.key_insights}")
