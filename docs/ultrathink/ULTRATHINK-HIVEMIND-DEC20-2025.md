# ULTRATHINK: HiveMind - Contribution-Guided Multi-Agent Optimization

**Date**: December 20, 2025
**arXiv**: 2512.06432
**Status**: Accepted to AAAI 2026
**Authors**: Yihan Xia, Taotao Wang, Shengli Zhang, Zhangyuhua Weng, Bin Cao, Soung Chang Liew

---

## PAPER SUMMARY

HiveMind addresses evaluation and optimization challenges in LLM-based multi-agent systems. It introduces **Contribution-Guided Online Prompt Optimization (CG-OPO)**, which autonomously refines agent prompts based on their quantified contributions.

### Key Innovation: DAG-Shapley Algorithm
- Uses **Shapley values** to measure individual agent effectiveness
- **DAG-Shapley** leverages Directed Acyclic Graph structure of agent workflows
- Reduces computational costs by **over 80%** while maintaining accuracy
- Axiomatically prunes non-viable coalitions through workflow structure awareness

### Results
- Superior performance in multi-agent stock-trading scenarios
- Automatically identifies underperforming agents for targeted improvement
- Enables scalable real-world deployment

---

## CHEROKEE AI FEDERATION RELEVANCE

### Direct Applications to 7-Specialist Council

| Paper Concept | Federation Equivalent | Enhancement Opportunity |
|---------------|----------------------|-------------------------|
| Contribution-Guided Optimization | Council voting weights | Dynamically adjust specialist influence based on contribution |
| DAG-Shapley | Cascaded voting | Measure which specialists add value in cascaded flow |
| Agent prompt refinement | Specialist prompts | Auto-tune specialist prompts based on vote quality |
| Underperformer detection | Specialist concerns | Identify when a specialist consistently flags false concerns |

### Implementation Ideas

#### 1. Council Contribution Tracking
```python
# Track specialist contribution to final decisions
class SpecialistContribution:
    def __init__(self, specialist_name):
        self.specialist = specialist_name
        self.votes_cast = 0
        self.votes_aligned_with_final = 0  # Did they vote with consensus?
        self.unique_concerns_valid = 0      # Concerns that changed outcome
        self.shapley_value = 0.0
```

#### 2. Dynamic Prompt Refinement
- If Crawdad flags too many false security concerns → refine prompt to be more specific
- If Gecko's performance assessments correlate with actual outcomes → increase weight
- If Turtle's 7GEN concerns are consistently validated → boost influence

#### 3. DAG Structure for Cascaded Voting
```
Query → Crawdad (Security) → Gecko (Technical) → Turtle (7GEN)
                ↓                    ↓                ↓
        Security OK?         Perf concerns?    Long-term OK?
                ↓                    ↓                ↓
        Peace Chief (Synthesis) ← ← ← ← ← ← ← ← ← ←
```

Apply DAG-Shapley to determine which path through the cascade adds most value.

### MSP Alignment

The paper's focus on **efficiency** (80% reduction in compute) aligns with Maximum Sustained Power:
- Don't burn tokens on redundant coalition calculations
- Prune agents that don't contribute meaningfully
- Sustained optimization over time, not one-shot tuning

---

## IMPLEMENTATION PLAN

### Phase 1: Contribution Tracking
- Add `contribution_score` field to `council_votes` table
- Track alignment between individual votes and final consensus
- Log when specialist concerns change outcomes

### Phase 2: Shapley Value Calculation
- Implement simplified DAG-Shapley for 7-specialist system
- Calculate weekly contribution scores per specialist
- Store in thermal memory for trend analysis

### Phase 3: Dynamic Prompt Refinement
- When specialist contribution drops below threshold → flag for prompt review
- When specialist consistently adds value → boost weight in voting
- TPM approval required for prompt changes

---

## Jr TASK REQUIREMENTS

1. Add contribution tracking to gateway.py
2. Create shapley_calculator.py for DAG-Shapley
3. Update council_votes schema with contribution fields
4. Create contribution_analysis.py for weekly reports

---

## RISKS AND CONCERNS

| Risk | Mitigation |
|------|------------|
| Over-optimization removes diversity | Keep minimum weight floor for all specialists |
| Gaming the contribution metric | Use multiple metrics, not just vote alignment |
| Computational overhead | DAG-Shapley specifically designed for efficiency |

---

## COUNCIL QUESTIONS (For Review)

1. Should specialist prompts be dynamically refined, or is human-in-loop required?
2. What's the minimum contribution threshold before flagging a specialist?
3. How do we prevent groupthink from high alignment scores?

---

*For Seven Generations - Cherokee AI Federation*
