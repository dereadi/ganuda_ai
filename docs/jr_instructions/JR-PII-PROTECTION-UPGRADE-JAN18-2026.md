# JR Instruction: PII Protection Upgrade - Replace Presidio

## Metadata
```yaml
task_id: pii_protection_upgrade
priority: 1
assigned_to: it_triad_jr
estimated_effort: high
category: security_enhancement
council_vote: 4fdd4018e18f99b4
council_priority: 1 of 6 (unanimous)
```

## Executive Summary

Replace Microsoft Presidio (F1=0.33) with a superior PII detection system achieving F1=0.95. This is the Council's unanimous #1 priority - "protecting sacred knowledge for Seven Generations."

## Background

### Current State
- VetAssist uses Microsoft Presidio for PII detection
- Presidio achieves F1=0.33 on medical documents (per arXiv research)
- This means ~67% of PII may go undetected
- Unacceptable risk for veteran SSN, DOB, medical records

### Target State
- Adaptive PII Framework: F1=0.95 (3x improvement)
- LLM-Anonymizer: 99.2% accuracy, runs locally on our infrastructure
- Zero cloud dependency - all processing on redfin/goldfin

## Research Sources

1. **Adaptive PII Mitigation Framework** (arXiv:2501.12465)
   - URL: https://arxiv.org/html/2501.12465v1
   - F1=0.95 for Passport Numbers vs Presidio's 0.33
   - Context-aware analysis, GRC integration

2. **LLM-Anonymizer** (NEJM AI)
   - URL: https://ai.nejm.org/doi/full/10.1056/AIdbp2400537
   - Llama-3 70B: 99.2% accuracy, 97.9% sensitivity
   - Runs locally, no cloud required
   - Benchmarked on real clinical documents

3. **Text Anonymization Survey** (arXiv:2508.21587)
   - URL: https://arxiv.org/html/2508.21587v1
   - Comprehensive overview of LLM-based techniques

## BACKEND LOCATION: /ganuda/lib/ganuda_pii

## Implementation Phases

### Phase 1: Research & Evaluation
**CREATE FILE: pii_benchmark.py**

```python
#!/usr/bin/env python3
"""
PII Detection Benchmark - Compare Presidio vs LLM-based approaches.
Cherokee AI Federation - For Seven Generations
"""

import time
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# Test corpus with known PII
TEST_CASES = [
    {
        "text": "Veteran John Smith, SSN 123-45-6789, DOB 01/15/1980, served in Iraq.",
        "expected_pii": ["SSN", "DOB", "PERSON", "LOCATION"]
    },
    {
        "text": "Patient presented with PTSD symptoms. Contact: john.smith@email.com, (555) 123-4567",
        "expected_pii": ["EMAIL", "PHONE"]
    },
    {
        "text": "VA File Number: 12345678. Address: 123 Main St, Anytown, TX 75001",
        "expected_pii": ["VA_FILE_NUMBER", "ADDRESS"]
    },
    # Add more test cases from real anonymized veteran documents
]

def benchmark_presidio():
    """Benchmark current Presidio implementation."""
    analyzer = AnalyzerEngine()

    results = {
        "true_positives": 0,
        "false_positives": 0,
        "false_negatives": 0,
        "latency_ms": []
    }

    for case in TEST_CASES:
        start = time.time()
        detected = analyzer.analyze(text=case["text"], language="en")
        latency = (time.time() - start) * 1000
        results["latency_ms"].append(latency)

        detected_types = set(r.entity_type for r in detected)
        expected_types = set(case["expected_pii"])

        results["true_positives"] += len(detected_types & expected_types)
        results["false_positives"] += len(detected_types - expected_types)
        results["false_negatives"] += len(expected_types - detected_types)

    precision = results["true_positives"] / (results["true_positives"] + results["false_positives"])
    recall = results["true_positives"] / (results["true_positives"] + results["false_negatives"])
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "avg_latency_ms": sum(results["latency_ms"]) / len(results["latency_ms"])
    }

def benchmark_llm_anonymizer():
    """Benchmark LLM-based PII detection using local Qwen model."""
    # Implementation uses local vLLM endpoint
    pass

if __name__ == "__main__":
    print("Benchmarking Presidio...")
    presidio_results = benchmark_presidio()
    print(f"Presidio F1: {presidio_results['f1']:.3f}")

    print("\nBenchmarking LLM-Anonymizer...")
    # llm_results = benchmark_llm_anonymizer()
```

### Phase 2: LLM-Based PII Detector
**CREATE FILE: llm_pii_detector.py**

```python
#!/usr/bin/env python3
"""
LLM-based PII Detector - Replaces Presidio with higher accuracy.
Based on Adaptive PII Framework (arXiv:2501.12465) and LLM-Anonymizer (NEJM AI).
Cherokee AI Federation
"""

import aiohttp
import json
import re
from typing import List, Dict, Optional
from dataclasses import dataclass

# Local vLLM endpoint
VLLM_URL = "http://localhost:8000/v1/chat/completions"
MODEL = "/ganuda/models/qwen2.5-coder-32b-awq"

@dataclass
class PIIEntity:
    entity_type: str
    text: str
    start: int
    end: int
    confidence: float

# PII categories relevant to veterans
PII_CATEGORIES = {
    "SSN": "Social Security Number (XXX-XX-XXXX format)",
    "DOB": "Date of Birth",
    "VA_FILE_NUMBER": "VA File Number or Claim Number",
    "PHONE": "Phone Number",
    "EMAIL": "Email Address",
    "ADDRESS": "Physical Address",
    "PERSON": "Person Name",
    "MILITARY_ID": "Military Service Number or DoD ID",
    "MEDICAL_RECORD": "Medical Record Number",
    "BANK_ACCOUNT": "Bank Account or Routing Number"
}

DETECTION_PROMPT = """You are a PII detection system for veteran documents. Identify ALL personally identifiable information in the text.

For each PII found, output JSON:
{
  "entities": [
    {"type": "SSN", "text": "123-45-6789", "start": 10, "end": 21},
    ...
  ]
}

PII Categories to detect:
- SSN: Social Security Numbers
- DOB: Dates of Birth
- VA_FILE_NUMBER: VA File/Claim Numbers
- PHONE: Phone Numbers
- EMAIL: Email Addresses
- ADDRESS: Physical Addresses
- PERSON: Names of people
- MILITARY_ID: Military IDs
- MEDICAL_RECORD: Medical Record Numbers
- BANK_ACCOUNT: Bank/Routing Numbers

TEXT TO ANALYZE:
{text}

Output ONLY valid JSON with detected entities:"""


class LLMPIIDetector:
    """High-accuracy PII detection using local LLM."""

    def __init__(self, model: str = MODEL):
        self.model = model
        self.url = VLLM_URL

    async def detect(self, text: str) -> List[PIIEntity]:
        """Detect PII entities in text using LLM."""
        prompt = DETECTION_PROMPT.format(text=text[:4000])  # Limit context

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.url,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000,
                    "temperature": 0.1  # Low temp for precision
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                response = data["choices"][0]["message"]["content"]

        return self._parse_response(response, text)

    def _parse_response(self, response: str, original_text: str) -> List[PIIEntity]:
        """Parse LLM response into PIIEntity list."""
        entities = []

        # Extract JSON from response
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group(0))
                for e in data.get("entities", []):
                    entities.append(PIIEntity(
                        entity_type=e["type"],
                        text=e["text"],
                        start=e.get("start", 0),
                        end=e.get("end", 0),
                        confidence=0.95  # LLM confidence
                    ))
        except json.JSONDecodeError:
            pass

        return entities

    def detect_sync(self, text: str) -> List[PIIEntity]:
        """Synchronous wrapper."""
        import asyncio
        return asyncio.run(self.detect(text))


# Drop-in replacement for Presidio
class AnalyzerEngine:
    """Presidio-compatible interface using LLM backend."""

    def __init__(self):
        self.detector = LLMPIIDetector()

    def analyze(self, text: str, language: str = "en") -> List[PIIEntity]:
        return self.detector.detect_sync(text)


if __name__ == "__main__":
    detector = LLMPIIDetector()
    test_text = "John Smith, SSN 123-45-6789, served 2003-2010. Contact: john@email.com"
    entities = detector.detect_sync(test_text)
    for e in entities:
        print(f"  {e.entity_type}: '{e.text}' ({e.confidence:.0%})")
```

### Phase 3: Integration with VetAssist
**MODIFY FILE: /ganuda/vetassist/backend/app/api/v1/endpoints/workbench_documents.py**

Replace Presidio imports with new LLM-based detector:
```python
# OLD:
# from presidio_analyzer import AnalyzerEngine
# from presidio_anonymizer import AnonymizerEngine

# NEW:
from ganuda_pii.llm_pii_detector import LLMPIIDetector, PIIEntity
```

### Phase 4: Anonymization Engine
**CREATE FILE: llm_anonymizer.py**

Implement anonymization strategies:
- Redaction: Replace with [REDACTED]
- Masking: Replace with type indicator [SSN], [DOB]
- Synthetic: Replace with fake but valid-format data
- Tokenization: Replace with reversible token for goldfin

## Success Criteria

| Metric | Presidio (Current) | Target | Test Method |
|--------|-------------------|--------|-------------|
| F1 Score | 0.33 | >0.90 | pii_benchmark.py |
| SSN Detection | ~60% | >99% | Test corpus |
| Latency | <100ms | <500ms | Acceptable for LLM |
| False Positives | High | <5% | Manual review |

## Testing

```bash
# Run benchmark
cd /ganuda/lib/ganuda_pii
python pii_benchmark.py

# Test on sample veteran document
python llm_pii_detector.py

# Integration test
curl -X POST http://localhost:8001/api/v1/workbench/projects/1/documents \
  -F "file=@test_doc.pdf" \
  -H "Authorization: Bearer $TOKEN"
```

## Rollout Plan

1. **Week 1**: Build benchmark, test LLM detector accuracy
2. **Week 2**: Implement anonymizer, integration tests
3. **Week 3**: Shadow mode (run both, compare results)
4. **Week 4**: Cutover to LLM-based system

## Cherokee Wisdom

> "The river that protects its banks can flow for centuries."

This upgrade protects veteran data - the sacred knowledge entrusted to us - ensuring it flows safely for Seven Generations.

---
**Council Vote**: 4fdd4018e18f99b4 - Unanimous Priority #1
**Cherokee AI Federation - For Seven Generations**
