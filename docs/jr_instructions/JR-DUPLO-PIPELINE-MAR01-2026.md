# JR Instruction: Duplo Pipeline (Multi-Enzyme Complexes)

**Task**: DUPLO-PIPELINE-001
**Title**: Create Duplo Pipeline — Multi-Enzyme Chaining
**Priority**: 3
**Assigned Jr**: Software Engineer Jr.

## Context

In biology, multi-enzyme complexes chain reactions: substrate → enzyme A → intermediate → enzyme B → product. The Duplo Pipeline does the same — chains composed enzymes with substrate passing.

Depends on: `lib/duplo/registry.py`, `lib/duplo/composer.py`

## Files

Create `lib/duplo/pipeline.py`

```python
"""
Duplo Pipeline — Multi-Enzyme Complexes
Cherokee AI Federation — The Living Cell Architecture

Chains Duplo enzymes so the product of one feeds as substrate to the next.
Each step is a composed enzyme. The pipeline handles:
  - Sequential chaining (output → input)
  - Error propagation (if one enzyme fails, pipeline stops)
  - Aggregate token accounting (total ATP consumed)
  - Per-step timing

Usage:
    from lib.duplo.pipeline import Pipeline
    from lib.duplo.composer import compose_enzyme

    pipe = Pipeline(
        name="security_review",
        caller_id="tpm_autonomic",
    )
    pipe.add_step("scan", compose_enzyme("crawdad_scan"))
    pipe.add_step("summarize", compose_enzyme("thermal_writer"))

    result = pipe.run(substrate="Review gateway.py for injection vulnerabilities")
    # result.products["scan"] = crawdad output
    # result.products["summarize"] = thermal writer output
    # result.total_tokens = aggregate
"""

import time
import json
import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("duplo.pipeline")


@dataclass
class StepResult:
    """Result from a single pipeline step."""
    name: str
    product: Optional[str]
    tokens: Dict[str, int]
    latency_ms: int
    success: bool
    error: Optional[str] = None


@dataclass
class PipelineResult:
    """Aggregate result from a full pipeline run."""
    name: str
    steps: List[StepResult]
    products: Dict[str, Optional[str]]
    total_tokens: Dict[str, int]
    total_latency_ms: int
    success: bool
    failed_step: Optional[str] = None


class Pipeline:
    """
    Multi-enzyme pipeline. Chains Duplo enzymes sequentially.

    Each enzyme receives the previous enzyme's product as its substrate.
    If a step fails, the pipeline stops and returns partial results.
    """

    def __init__(self, name: str, caller_id: str = "unknown"):
        self.name = name
        self.caller_id = caller_id
        self._steps: List[tuple] = []  # (name, enzyme_callable)

    def add_step(self, name: str, enzyme: Callable) -> "Pipeline":
        """Add an enzyme step to the pipeline. Returns self for chaining."""
        self._steps.append((name, enzyme))
        return self

    def run(self, substrate: str) -> PipelineResult:
        """
        Execute the pipeline. Each step's product becomes the next step's substrate.
        """
        start = time.time()
        steps: List[StepResult] = []
        products: Dict[str, Optional[str]] = {}
        total_input = 0
        total_output = 0
        current_substrate = substrate
        failed_step = None

        for step_name, enzyme in self._steps:
            logger.info(f"Pipeline '{self.name}' step '{step_name}' starting")

            result = enzyme(current_substrate)

            step = StepResult(
                name=step_name,
                product=result.get("product"),
                tokens=result.get("tokens", {"input": 0, "output": 0, "total": 0}),
                latency_ms=result.get("latency_ms", 0),
                success=result.get("success", False),
                error=result.get("error"),
            )
            steps.append(step)
            products[step_name] = step.product

            total_input += step.tokens.get("input", 0)
            total_output += step.tokens.get("output", 0)

            if not step.success:
                failed_step = step_name
                logger.error(f"Pipeline '{self.name}' failed at step '{step_name}': {step.error}")
                break

            # Pass product as substrate to next step
            current_substrate = step.product or ""

        total_latency = int((time.time() - start) * 1000)

        pipeline_result = PipelineResult(
            name=self.name,
            steps=steps,
            products=products,
            total_tokens={
                "input": total_input,
                "output": total_output,
                "total": total_input + total_output,
            },
            total_latency_ms=total_latency,
            success=failed_step is None,
            failed_step=failed_step,
        )

        # Log aggregate to token_ledger
        self._log_pipeline(pipeline_result)

        return pipeline_result

    def _log_pipeline(self, result: PipelineResult):
        """Log aggregate pipeline result to token_ledger."""
        try:
            from lib.ganuda_db import get_connection
            conn = get_connection()
            try:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO token_ledger
                    (model, caller_id, call_type, input_tokens, output_tokens,
                     latency_ms, metadata)
                    VALUES (%s, %s, 'pipeline', %s, %s, %s, %s)
                """, (
                    "pipeline:" + self.name,
                    self.caller_id,
                    result.total_tokens["input"],
                    result.total_tokens["output"],
                    result.total_latency_ms,
                    json.dumps({
                        "pipeline": self.name,
                        "steps": [s.name for s in result.steps],
                        "success": result.success,
                        "failed_step": result.failed_step,
                    }),
                ))
                conn.commit()
            finally:
                conn.close()
        except Exception as e:
            logger.warning(f"Failed to log pipeline result: {e}")
```

## Verification

1. Import test: `python3 -c "from lib.duplo.pipeline import Pipeline; p = Pipeline('test'); print('OK')"`
2. With vLLM running, chain two enzymes:
   ```text
   python3 -c "
   from lib.duplo.composer import compose_enzyme
   from lib.duplo.pipeline import Pipeline
   p = Pipeline('test_chain', 'verification')
   p.add_step('analyze', compose_enzyme('test_echo'))
   p.add_step('summarize', compose_enzyme('test_echo'))
   r = p.run('Hello federation')
   print(f'Success: {r.success}, Steps: {len(r.steps)}, Tokens: {r.total_tokens}')
   "
   ```
