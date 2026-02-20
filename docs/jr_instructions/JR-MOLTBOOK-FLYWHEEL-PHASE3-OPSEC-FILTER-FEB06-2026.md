# JR-MOLTBOOK-FLYWHEEL-PHASE3-OPSEC-FILTER-FEB06-2026

## Task
Extend the Moltbook proxy output_filter.py with research-specific OPSEC patterns and query sanitization capabilities for the Research Jr + Moltbook Flywheel integration.

## Context
The Research Jr component generates outbound queries to external search engines (SearXNG) and synthesizes results for public posting. Phase 3 ensures that research queries are sanitized before leaving our network and that research results are filtered before response synthesis. This prevents accidental exposure of internal terminology, architecture details, and infrastructure specifics during the research-to-post pipeline.

**Priority:** P1 - Security Critical
**Specialist:** Crawdad (Security)
**Dependencies:** Phase 1 (Inbound Detector), Phase 2 (Research-Aware Reasoner)

## Current State
The existing output_filter.py at `/ganuda/services/moltbook_proxy/output_filter.py` already has:
- Internal IP blocking (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
- Internal path blocking (/ganuda/, /home/dereadi/)
- Database credential blocking (jawaseatlasers, zammad_production)
- Infrastructure scale patterns (\b6.node\b, \b7.specialist\b, 19,?808, \b96.?GB\b, :5432\b, PGPASSWORD=)
- Proprietary technology names (thermal.memor, magrpo, jr.executor, etc.)
- Personnel names (dereadi, PatoGravy, Darrell)

## Steps

### Step 1: Add Research-Specific Blocked Patterns
Add these new patterns to the BLOCKED_PATTERNS list:

```python
# Research-specific patterns (Phase 3)

# Table names - internal database schema
re.compile(r'\bthermal_memory_archive\b', re.IGNORECASE),
re.compile(r'\bmoltbook_post_queue\b', re.IGNORECASE),
re.compile(r'\bvetassist_cfr_conditions\b', re.IGNORECASE),
re.compile(r'\bjr_task_queue\b', re.IGNORECASE),
re.compile(r'\bkanban_cards\b', re.IGNORECASE),
re.compile(r'\bpheromone_trails\b', re.IGNORECASE),
re.compile(r'\bcouncil_votes\b', re.IGNORECASE),

# Additional database names
re.compile(r'\bcherokee_federation\b', re.IGNORECASE),
re.compile(r'\bamem_store\b', re.IGNORECASE),

# Partial credential patterns (fragments that might leak)
re.compile(r'password\s*[:=]\s*[\'"][^\'"]{4,}', re.IGNORECASE),
re.compile(r'api[_-]?key\s*[:=]\s*[\'"][^\'"]{8,}', re.IGNORECASE),
re.compile(r'token\s*[:=]\s*[\'"][^\'"]{16,}', re.IGNORECASE),

# Service ports that reveal architecture
re.compile(r':11434\b'),  # Ollama
re.compile(r':8888\b'),   # Research API
re.compile(r':3000\b'),   # Grafana/Frontend
re.compile(r':9090\b'),   # Prometheus

# Internal network ranges (VLAN specific)
re.compile(r'vlan\s*\d+', re.IGNORECASE),
re.compile(r'\.local\b'),

# Research infrastructure specifics
re.compile(r'\bsearxng\b', re.IGNORECASE),
re.compile(r'\bii-researcher\b', re.IGNORECASE),
re.compile(r'research.worker', re.IGNORECASE),
```

### Step 2: Implement Query Sanitization Function
Add a new function to sanitize outbound research queries:

```python
# Query sanitization mappings for outbound research
QUERY_SANITIZATIONS = {
    # Organization names
    r'\bCherokee\s+AI\s+Federation\b': 'AI agent collective',
    r'\bCherokee\s+Federation\b': 'distributed AI system',
    r'\bSeven\s+Generations\b': 'long-term planning framework',

    # Technology names
    r'\bthermal\s+memor(y|ies)\b': 'persistent memory system',
    r'\bpheromone\s+(trail|decay|signal)s?\b': 'coordination signals',
    r'\bstigmergic\b': 'indirect coordination',
    r'\bmagrpo\b': 'momentum tracking',
    r'\bsmart.?extract(or|ion)?\b': 'data extraction',

    # Node names
    r'\bredfin\b': 'compute-node-1',
    r'\bbluefin\b': 'compute-node-2',
    r'\bgreenfin\b': 'compute-node-3',
    r'\bsilverfin\b': 'compute-node-4',
    r'\bblackfin\b': 'compute-node-5',
    r'\bsasass\d?\b': 'storage-node',

    # Specialist names in queries
    r'\b(Crawdad|Gecko|Turtle|Eagle[\s-]?Eye|Spider|Peace[\s-]?Chief|Raven)\b': 'specialist agent',

    # Personnel (should not appear in queries but safety check)
    r'\bdereadi\b': 'user',
    r'\bDarrell\b': 'operator',
}


def sanitize_research_query(query: str) -> Tuple[str, List[str]]:
    """
    Sanitize an outbound research query before it leaves our network.

    Replaces internal terminology with generic equivalents.

    Args:
        query: The raw research query

    Returns:
        Tuple of (sanitized_query, list_of_replacements_made)
    """
    if not query:
        return query, []

    sanitized = query
    replacements = []

    for pattern, replacement in QUERY_SANITIZATIONS.items():
        regex = re.compile(pattern, re.IGNORECASE)
        matches = regex.findall(sanitized)
        if matches:
            sanitized = regex.sub(replacement, sanitized)
            replacements.append(f'{pattern} -> {replacement} ({len(matches)}x)')

    if replacements:
        logger.info(f'Query sanitized: {len(replacements)} replacement(s)')
        for r in replacements:
            logger.debug(f'  - {r}')

    return sanitized, replacements
```

### Step 3: Implement Research Result Filter
Add a function to filter research results before synthesis:

```python
def filter_research_results(results: List[str]) -> Tuple[List[str], List[dict]]:
    """
    Filter research results before they are used in response synthesis.

    Removes any results that contain blocked patterns and logs for review.

    Args:
        results: List of research result strings

    Returns:
        Tuple of (filtered_results, blocked_entries_log)
    """
    if not results:
        return [], []

    filtered = []
    blocked_log = []

    for i, result in enumerate(results):
        is_safe, violations = validate_outbound(result)

        if is_safe:
            filtered.append(result)
        else:
            blocked_log.append({
                'index': i,
                'preview': result[:100] + '...' if len(result) > 100 else result,
                'violations': violations,
                'timestamp': __import__('datetime').datetime.utcnow().isoformat()
            })
            logger.warning(f'Research result {i} blocked: {len(violations)} violation(s)')

    if blocked_log:
        logger.warning(f'Filtered {len(blocked_log)}/{len(results)} research results')

    return filtered, blocked_log
```

### Step 4: Add Security Audit Logging
Add a function to log blocked content for security review:

```python
import json
from pathlib import Path
from datetime import datetime

SECURITY_LOG_PATH = Path('/ganuda/logs/moltbook_opsec_blocks.jsonl')


def log_blocked_content(content_type: str, content_preview: str,
                        violations: List[str], source: str = 'unknown') -> None:
    """
    Log blocked content for security review.

    Creates append-only JSONL log for security audit trail.

    Args:
        content_type: Type of content ('query', 'result', 'outbound')
        content_preview: First 200 chars of blocked content
        violations: List of violation descriptions
        source: Source identifier (e.g., 'research_jr', 'moltbook_post')
    """
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'content_type': content_type,
        'source': source,
        'preview': content_preview[:200] if content_preview else '',
        'violations': violations,
        'violation_count': len(violations)
    }

    try:
        # Ensure log directory exists
        SECURITY_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

        with open(SECURITY_LOG_PATH, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

        logger.info(f'Security block logged: {content_type} from {source}')
    except Exception as e:
        logger.error(f'Failed to write security log: {e}')
```

### Step 5: Update validate_outbound to Use Security Logging
Modify the existing `validate_outbound` function to call the security logger:

```python
def validate_outbound(text: str, source: str = 'unknown') -> Tuple[bool, List[str]]:
    """
    Validate outbound content for information leaks.

    Args:
        text: Content to validate
        source: Source identifier for logging

    Returns:
        Tuple of (is_safe, list_of_violations)
    """
    if not text:
        return True, []

    violations = []

    for pattern in BLOCKED_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            violations.append(f'blocked_pattern: {pattern.pattern} (found {len(matches)}x)')

    # Check for sensitive terms in what looks like technical context
    for term, description in SENSITIVE_TERMS.items():
        if term.lower() in text.lower():
            context_words = ['running', 'using', 'deployed', 'installed', 'configured', 'our']
            surrounding = text.lower()
            for cw in context_words:
                if cw in surrounding and term.lower() in surrounding:
                    violations.append(f'sensitive_term_in_context: {term} ({description})')
                    break

    is_safe = len(violations) == 0

    if not is_safe:
        logger.warning(f'Output filter blocked: {len(violations)} violation(s)')
        for v in violations:
            logger.warning(f'  - {v}')

        # Log to security audit file
        log_blocked_content(
            content_type='outbound',
            content_preview=text[:200],
            violations=violations,
            source=source
        )

    return is_safe, violations
```

### Step 6: Add Convenience Wrapper for Research Pipeline
Add a high-level function for the research pipeline integration:

```python
def process_research_outbound(query: str, results: List[str],
                               synthesis: str) -> Tuple[str, List[str], str, dict]:
    """
    Process all outbound content for the research pipeline.

    Sanitizes query, filters results, validates synthesis.

    Args:
        query: Raw research query
        results: Raw research results
        synthesis: Draft synthesis text

    Returns:
        Tuple of (sanitized_query, filtered_results, validated_synthesis, report)
    """
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'query_sanitizations': [],
        'results_blocked': 0,
        'synthesis_safe': False,
        'synthesis_violations': []
    }

    # Step 1: Sanitize query
    sanitized_query, query_replacements = sanitize_research_query(query)
    report['query_sanitizations'] = query_replacements

    # Step 2: Filter results
    filtered_results, blocked_log = filter_research_results(results)
    report['results_blocked'] = len(blocked_log)
    if blocked_log:
        for entry in blocked_log:
            log_blocked_content(
                content_type='result',
                content_preview=entry['preview'],
                violations=entry['violations'],
                source='research_pipeline'
            )

    # Step 3: Validate synthesis
    synthesis_safe, synthesis_violations = validate_outbound(synthesis, source='research_synthesis')
    report['synthesis_safe'] = synthesis_safe
    report['synthesis_violations'] = synthesis_violations

    # If synthesis is not safe, attempt to sanitize it
    validated_synthesis = synthesis
    if not synthesis_safe:
        # Re-run sanitization on synthesis as a remediation attempt
        validated_synthesis, _ = sanitize_research_query(synthesis)
        # Re-validate
        still_safe, remaining = validate_outbound(validated_synthesis, source='research_synthesis_retry')
        if not still_safe:
            logger.error(f'Synthesis still contains {len(remaining)} violation(s) after sanitization')
            validated_synthesis = None  # Block entirely

    return sanitized_query, filtered_results, validated_synthesis, report
```

## Verification

1. **Pattern Test:** Run the following to verify new patterns work:
```bash
cd /ganuda/services/moltbook_proxy
python3 -c "
from output_filter import validate_outbound, sanitize_research_query

# Test blocked patterns
test_cases = [
    'Check the thermal_memory_archive table',
    'Query moltbook_post_queue for pending posts',
    'Connect to 192.168.30.5',
    'Using /ganuda/services/config',
    'Port :11434 is for Ollama',
]

print('=== Blocked Pattern Tests ===')
for tc in test_cases:
    safe, violations = validate_outbound(tc)
    print(f'BLOCKED: {tc[:50]}...' if not safe else f'PASSED: {tc[:50]}')

# Test sanitization
print('\n=== Query Sanitization Tests ===')
queries = [
    'How does the Cherokee AI Federation handle memory?',
    'What is thermal memory in distributed AI?',
    'Search for redfin server configuration',
]
for q in queries:
    sanitized, replacements = sanitize_research_query(q)
    print(f'Original: {q}')
    print(f'Sanitized: {sanitized}')
    print()
"
```

2. **Integration Test:** Verify the research pipeline function:
```bash
python3 -c "
from output_filter import process_research_outbound

query = 'How does Cherokee AI Federation thermal memory work?'
results = [
    'Result about AI systems',
    'Internal: Check /ganuda/services for config',
    'Generic result about memory',
]
synthesis = 'The system uses thermal memory for persistence.'

q, r, s, report = process_research_outbound(query, results, synthesis)
print(f'Sanitized query: {q}')
print(f'Filtered results: {len(r)}/{len(results)}')
print(f'Synthesis safe: {s is not None}')
print(f'Report: {report}')
"
```

3. **Log Verification:** Check security log is created:
```bash
ls -la /ganuda/logs/moltbook_opsec_blocks.jsonl
tail -5 /ganuda/logs/moltbook_opsec_blocks.jsonl 2>/dev/null || echo "No blocks logged yet"
```

## Files Modified
- `/ganuda/services/moltbook_proxy/output_filter.py` - Extended with research OPSEC capabilities

## Files Created
- `/ganuda/logs/moltbook_opsec_blocks.jsonl` - Security audit log (created on first block)

## Dependencies
- Phase 1: JR-MOLTBOOK-FLYWHEEL-PHASE1-INBOUND-DETECTOR-FEB06-2026.md
- Phase 2: JR-MOLTBOOK-FLYWHEEL-PHASE2-RESEARCH-REASONER-FEB06-2026.md

## Rollback
To rollback, restore from git:
```bash
cd /ganuda/services/moltbook_proxy
git checkout HEAD -- output_filter.py
```

## Notes
- Preserve all existing patterns in BLOCKED_PATTERNS - they are production-tested
- The security log uses JSONL format for easy parsing with jq
- Query sanitization is case-insensitive but preserves original case where possible
- If synthesis fails validation after sanitization, return None to block the post entirely
- Log rotation for moltbook_opsec_blocks.jsonl should be configured in logrotate

---
*For Seven Generations*
*Crawdad Security Review: Required before deployment*
