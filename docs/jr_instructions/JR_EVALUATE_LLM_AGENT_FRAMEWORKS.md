# Jr Task: Evaluate LLM Agent Frameworks for Cherokee AI Integration

**Task ID:** task-evaluate-agent-frameworks-001
**Priority:** P2 (Research & Enhancement)
**Node:** sasass (evaluation), redfin (integration testing)
**Created:** December 22, 2025
**Source:** https://github.com/kaushikb11/awesome-llm-agents
**TPM:** Cherokee AI Federation

---

## Executive Summary

Evaluate three high-potential LLM agent frameworks from the awesome-llm-agents repository for potential integration with Cherokee AI infrastructure. Focus on frameworks that complement (not replace) our existing Jr specialist system.

---

## Frameworks to Evaluate

### 1. Smolagents (Hugging Face) - 24.4K Stars

**Repository:** https://github.com/huggingface/smolagents
**License:** Apache-2.0

**Why Evaluate:**
- Minimalist, code-first approach ideal for edge nodes (sasass, greenfin)
- Multi-agent orchestration built-in
- LLM provider flexibility (can use our vLLM backend)
- Tool integration patterns we could adopt

**Cherokee AI Fit:**
- Could power lightweight Jr agents on Mac nodes
- Code-first aligns with our instruction-based Jr system
- Minimal dependencies = easier deployment

**Evaluation Tasks:**
```bash
# On sasass
cd /ganuda/experiments
git clone https://github.com/huggingface/smolagents.git
cd smolagents

# Create venv
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Test with our vLLM backend
python3 << 'EOF'
from smolagents import CodeAgent, LiteLLMModel

# Point to Cherokee AI vLLM
model = LiteLLMModel(
    model_id="openai/nvidia/NVIDIA-Nemotron-Nano-9B-v2",
    api_base="http://192.168.132.223:8000/v1",
    api_key="not-needed"
)

agent = CodeAgent(tools=[], model=model)
result = agent.run("What is 2 + 2?")
print(f"Result: {result}")
EOF
```

**Success Criteria:**
- [ ] Smolagent can use our vLLM as backend
- [ ] Agent execution time < 5 seconds for simple tasks
- [ ] Memory footprint < 500MB on Mac nodes
- [ ] Can integrate with thermal memory for context

---

### 2. Pydantic AI - 13.9K Stars

**Repository:** https://github.com/pydantic/pydantic-ai
**License:** MIT

**Why Evaluate:**
- Production-grade, type-safe development
- Structured responses (we need this for Council votes)
- Dependency injection system
- Multi-model support

**Cherokee AI Fit:**
- Could replace ad-hoc JSON parsing in gateway.py
- Type-safe specialist responses
- Better error handling for Council votes
- Structured output validation

**Evaluation Tasks:**
```bash
# On redfin
cd /ganuda/experiments
pip install pydantic-ai

# Test structured Council response
python3 << 'EOF'
from pydantic import BaseModel
from pydantic_ai import Agent

class CouncilVote(BaseModel):
    specialist: str
    recommendation: str  # PROCEED, HALT, DEFER
    confidence: float
    concerns: list[str]
    reasoning: str

agent = Agent(
    'openai:nvidia/NVIDIA-Nemotron-Nano-9B-v2',
    result_type=CouncilVote,
    system_prompt="You are Crawdad, the Security Specialist for Cherokee AI."
)

# This should return structured, validated output
result = agent.run_sync(
    "Should we deploy a new API endpoint without authentication?",
    model_settings={'base_url': 'http://localhost:8000/v1'}
)
print(result.data)
EOF
```

**Success Criteria:**
- [ ] Pydantic AI works with vLLM OpenAI-compatible API
- [ ] Structured responses validate correctly
- [ ] Can define specialist response schemas
- [ ] Error messages are actionable when validation fails

---

### 3. Agentic Radar - 848 Stars

**Repository:** https://github.com/splx-ai/agentic-radar
**License:** Apache-2.0

**Why Evaluate:**
- Security scanner specifically for agentic workflows
- CVE and OWASP vulnerability detection
- Interactive reports with remediation suggestions
- Could audit our Jr task execution system

**Cherokee AI Fit:**
- Security audit of Jr instruction execution
- Scan gateway.py for injection vulnerabilities
- Validate thermal memory access patterns
- Crawdad (Security Specialist) enhancement

**Evaluation Tasks:**
```bash
# On bluefin or redfin
cd /ganuda/experiments
git clone https://github.com/splx-ai/agentic-radar.git
cd agentic-radar
pip install -e .

# Scan our gateway
agentic-radar scan /ganuda/services/llm_gateway/gateway.py --output gateway_security_report.html

# Scan Jr executor
agentic-radar scan /ganuda/jr_executor/ --output jr_executor_security_report.html

# Review reports
# Copy to local for viewing: scp dereadi@redfin:/ganuda/experiments/agentic-radar/*.html .
```

**Success Criteria:**
- [ ] Scanner runs without errors on our codebase
- [ ] Identifies at least 3 areas for security improvement
- [ ] Reports are actionable (not just FUD)
- [ ] Can integrate into CI/CD or nightly checks

---

## Bonus Evaluations (If Time Permits)

### 4. Cache-to-Cache (C2C) - 87 Stars

**Why:** Direct semantic KV-Cache communication between LLMs - could revolutionize how Jr agents share context without going through thermal memory.

```bash
git clone https://github.com/xxx/cache-to-cache  # Get actual URL
# Evaluate if KV-cache sharing works with vLLM
```

### 5. saplings - 269 Stars

**Why:** Tree search algorithms for reasoning - could improve Council decision quality.

```bash
pip install saplings
# Test MCTS or beam search on Council deliberation
```

---

## Evaluation Report Template

For each framework, document:

```markdown
## [Framework Name] Evaluation

**Date:** YYYY-MM-DD
**Evaluator:** [Jr Name]
**Node:** [Where tested]

### Installation
- Dependencies installed: [list]
- Install time: [X minutes]
- Disk space: [X MB]

### Compatibility
- Works with vLLM: [Yes/No/Partial]
- Works with thermal memory: [Yes/No/N/A]
- Python version compatibility: [3.x]

### Performance
- Simple task latency: [X ms]
- Memory usage: [X MB]
- CPU usage: [X%]

### Integration Potential
- Gateway enhancement: [High/Medium/Low/None]
- Jr system enhancement: [High/Medium/Low/None]
- Security improvement: [High/Medium/Low/None]

### Recommendation
- [ ] ADOPT - Integrate into production
- [ ] TRIAL - Limited pilot deployment
- [ ] ASSESS - Continue evaluation
- [ ] HOLD - Not suitable at this time

### Notes
[Free-form observations, gotchas, tips]
```

---

## Deliverables

1. **Evaluation Reports** - One per framework in `/ganuda/docs/evaluations/`
2. **Integration PoC** - If framework scores ADOPT/TRIAL, create proof-of-concept
3. **Jr Instruction** - If integration approved, create implementation Jr instruction
4. **Thermal Memory Entry** - Store key findings for future reference

---

## Timeline

| Phase | Task | Est. Effort |
|-------|------|-------------|
| 1 | Install and test Smolagents | 2-3 hours |
| 2 | Install and test Pydantic AI | 2-3 hours |
| 3 | Install and test Agentic Radar | 1-2 hours |
| 4 | Write evaluation reports | 1-2 hours |
| 5 | Council review of findings | 30 min |

---

## Council Review Prompt

After evaluation, submit findings for Council vote:

```bash
curl -X POST http://192.168.132.223:8080/v1/council/vote \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" \
  -d '{
    "question": "Based on Jr evaluation, which frameworks should we integrate into Cherokee AI?",
    "context": "[Paste evaluation summary here]",
    "options": [
      "Integrate Smolagents for edge Jr agents",
      "Integrate Pydantic AI for structured responses",
      "Integrate Agentic Radar for security scanning",
      "Integrate multiple frameworks",
      "None - current architecture sufficient"
    ]
  }'
```

---

## References

- awesome-llm-agents: https://github.com/kaushikb11/awesome-llm-agents
- Smolagents docs: https://huggingface.co/docs/smolagents
- Pydantic AI docs: https://ai.pydantic.dev/
- Agentic Radar: https://github.com/splx-ai/agentic-radar

---

*For Seven Generations - Cherokee AI Federation*
