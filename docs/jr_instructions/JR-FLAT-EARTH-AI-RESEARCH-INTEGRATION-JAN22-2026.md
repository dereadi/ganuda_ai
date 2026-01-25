# JR: Flat Earth AI Research Integration

**Date:** January 22, 2026
**Priority:** Medium
**Type:** Research + Architecture Enhancement
**Assigned To:** Research Jr

## Objective

Pull and analyze two recent AI research papers to identify architectural enhancements for Cherokee AI Federation, specifically for thermal memory, council voting, and causal reasoning.

## Papers to Retrieve and Analyze

### Paper 1: Riemannian Liquid Spatio-Temporal Graph Network (RLSTG)

**Authors:** Liangsi Lu, Jingchao Wang, Zhaorong Dai, Hanqian Liu, Yang Shi
**Institutions:** Guangdong University of Technology, Peking University, Sun Yat-Sen University, South China Agricultural University

**Search Terms:**
- "Riemannian Liquid Spatio-Temporal Graph Network"
- "RLSTG continuous dynamics"
- Authors: Liangsi Lu, Jingchao Wang

**Focus Areas:**
1. How do they implement continuous dynamics on Riemannian manifolds?
2. What differential equations are used for temporal evolution?
3. How is the "curved" topology of data represented?
4. Can we apply this to thermal_relationships for causal reasoning?
5. What is their approach to preventing "impossible trajectories"?

### Paper 2: Are LLMs Smarter Than Chimpanzees?

**Authors:** Dingyi Yang, Junqi Zhao, Xue Li, Ce Li, Boyang Li
**Institution:** Nanyang Technological University, USTC, China University of Mining

**Search Terms:**
- "Are LLMs Smarter Than Chimpanzees"
- "LLM perspective taking knowledge state"
- "Theory of Mind LLM evaluation"

**Focus Areas:**
1. What specific ToM (Theory of Mind) tests do they use?
2. How do they measure "epistemic isolation" failures?
3. What architectural changes would enable belief/knowledge separation?
4. Can we add ToM benchmarks to council vote evaluation?
5. What is their proposed solution for the "telepathic" attention problem?

## Deliverables

### 1. Paper Summaries (Markdown)
Create `/ganuda/docs/research/RLSTG-PAPER-ANALYSIS-JAN2026.md` and `/ganuda/docs/research/CHIMPANZEE-TOM-PAPER-ANALYSIS-JAN2026.md`

### 2. Cherokee AI Enhancement Proposals

For each paper, identify:
- **Direct Implementations**: Changes we can make now
- **Research Items**: Things requiring further investigation
- **Validation Tests**: How to verify our architecture against their findings

### 3. Specific Code Enhancement Recommendations

| Component | Current State | Proposed Enhancement | Paper Source |
|-----------|--------------|---------------------|--------------|
| thermal_relationships | Discrete confidence scores | Continuous manifold metrics? | RLSTG |
| council voting | Specialist isolation | Epistemic firewalling | Chimpanzee |
| thermal_clauses | IF-THEN logic | Causal direction encoding | RLSTG |

### 4. Council Vote Analysis

Run a council vote on proposed enhancements:
```
POST /v1/council/vote
{
  "question": "Should we implement Riemannian metrics in thermal_relationships for causal reasoning?",
  "context": "[Paper findings summary]"
}
```

## Resources

- ArXiv search: https://arxiv.org/search/
- Semantic Scholar: https://www.semanticscholar.org/
- Google Scholar for citations
- Cherokee AI Gateway: http://192.168.132.223:8080

## Success Criteria

- [ ] Both papers retrieved and analyzed
- [ ] Enhancement proposals documented
- [ ] Council vote recorded
- [ ] At least 2 actionable code changes identified
- [ ] KB article updated with findings

## For Seven Generations

This research validates our architectural choices while revealing opportunities to strengthen epistemic isolation and causal reasoning - capabilities that will compound over generations of AI development.
