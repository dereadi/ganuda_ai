# JR Instruction: VetAssist Research Executor Fix

**JR ID:** JR-VETASSIST-RESEARCH-EXECUTOR-FIX-JAN27-2026
**Priority:** P2 - User-Facing Bug
**Assigned To:** Software Engineer Jr.
**Ultrathink:** ULTRATHINK-VETASSIST-EXECUTOR-BUGS-JAN27-2026.md

---

## Problem Statement

VetAssist research tasks complete in 5 seconds with empty results because:
1. No URLs are extracted from instructions (source names like "VA.gov" aren't URLs)
2. Topic extraction patterns don't match "QUESTION:" format
3. No worker daemon running for `it_triad_jr`

---

## Task 1: Add Source-to-URL Mapping

**File:** `/ganuda/jr_executor/research_task_executor.py`

Add this constant after the imports (around line 20):

```python
# VetAssist authoritative source URLs
VETASSIST_SOURCE_URLS = {
    'va.gov': [
        'https://www.va.gov/disability/eligibility/',
        'https://www.va.gov/disability/how-to-file-claim/',
    ],
    '38cfr': [
        'https://www.ecfr.gov/current/title-38/chapter-I/part-3',
        'https://www.ecfr.gov/current/title-38/chapter-I/part-4',
    ],
    'bva_decisions': [
        'https://www.va.gov/vetapp/',
    ],
    'cck-law.com': [
        'https://cck-law.com/blog/',
    ],
    'vaclaimsinsider.com': [
        'https://vaclaimsinsider.com/va-disability-ratings/',
    ],
    'hillandponton.com': [
        'https://www.hillandponton.com/va-disability-calculator/',
    ],
}
```

---

## Task 2: Add VetAssist Source Detection

**File:** `/ganuda/jr_executor/research_task_executor.py`

Add this method to the `ResearchTaskExecutor` class (after `_extract_arxiv_ids`):

```python
def _extract_vetassist_urls(self, instructions: str) -> List[str]:
    """
    Extract URLs for VetAssist research tasks based on source names.

    VetAssist instructions reference sources by name (e.g., "VA.gov", "38 CFR")
    rather than URLs. This method maps source names to actual URLs.
    """
    urls = []
    instructions_lower = instructions.lower()

    # Check if this is a VetAssist research task
    if 'veteran research task' not in instructions_lower:
        return urls

    # Map source names to URLs
    for source_name, source_urls in VETASSIST_SOURCE_URLS.items():
        if source_name.lower() in instructions_lower:
            urls.extend(source_urls)
            print(f"[ResearchTaskExecutor] Added {len(source_urls)} URLs for source: {source_name}")

    return urls
```

---

## Task 3: Update execute_research_task to Use VetAssist URLs

**File:** `/ganuda/jr_executor/research_task_executor.py`

Modify `execute_research_task` method. After line 48 (`arxiv_ids = self._extract_arxiv_ids(instructions)`), add:

```python
        # Extract VetAssist source URLs
        vetassist_urls = self._extract_vetassist_urls(instructions)
        urls.extend(vetassist_urls)

        print(f"[ResearchTaskExecutor] Found {len(urls)} URLs, {len(topics)} topics, {len(arxiv_ids)} ArXiv IDs, {len(vetassist_urls)} VetAssist sources")
```

---

## Task 4: Add QUESTION Pattern to Topic Extraction

**File:** `/ganuda/jr_executor/research_task_executor.py`

Modify `_extract_topics` method (around line 195). Add these patterns:

```python
    def _extract_topics(self, text: str) -> List[str]:
        """Extract research topics from instruction text."""
        patterns = [
            r'Paper \d+:\s*([^\n]+)',
            r'Research:\s*([^\n]+)',
            r'Topic:\s*([^\n]+)',
            r'Analyze:\s*([^\n]+)',
            r'QUESTION:\s*([^\n]+)',  # VetAssist format
            r'Question:\s*([^\n]+)',  # Case variations
        ]
        topics = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            topics.extend(matches)
        return topics
```

---

## Task 5: Add Council Fallback for No-Source Research

**File:** `/ganuda/jr_executor/research_task_executor.py`

At the end of `execute_research_task`, before the return (around line 155), add fallback:

```python
        # If no sources found, try Council consultation as fallback
        if successful_fetches == 0 and len(results) == 0:
            print("[ResearchTaskExecutor] No sources fetched, attempting Council fallback")
            try:
                import requests
                council_response = requests.post(
                    'http://192.168.132.223:8080/v1/council/vote',
                    headers={
                        'Authorization': 'Bearer ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'topic': title,
                        'question': instructions[:1000],
                        'context': 'VetAssist research request'
                    },
                    timeout=60
                )
                if council_response.status_code == 200:
                    council_data = council_response.json()
                    council_summary = council_data.get('synthesis', council_data.get('final_answer', 'Council consulted'))

                    # Add council result to summary
                    summary_content += f"\n\n## Council Consultation\n\n{council_summary}\n"

                    # Update summary file
                    with open(summary_file, 'w') as f:
                        f.write(summary_content)

                    artifacts.append({
                        'type': 'council_consultation',
                        'synthesis': council_summary[:500]
                    })

                    # Mark as partial success since Council provided response
                    return {
                        'success': True,
                        'artifacts': artifacts,
                        'steps_executed': steps_executed + [{'type': 'council_fallback', 'success': True}],
                        'summary': f"Council consulted (no web sources). Report: {summary_file}",
                        'sources_fetched': 0,
                        'council_consulted': True
                    }
            except Exception as council_error:
                print(f"[ResearchTaskExecutor] Council fallback failed: {council_error}")
```

---

## Task 6: Create Systemd Service for VetAssist Worker

**File:** `/ganuda/scripts/systemd/jr-vetassist-worker.service`

```ini
[Unit]
Description=Jr Queue Worker for VetAssist Research Tasks
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/jr_executor
Environment=CHEROKEE_DB_HOST=192.168.132.222
Environment=CHEROKEE_DB_NAME=zammad_production
Environment=CHEROKEE_DB_USER=claude
Environment=CHEROKEE_DB_PASS=jawaseatlasers2
ExecStart=/usr/bin/python3 /ganuda/jr_executor/jr_queue_worker.py "it_triad_jr"
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

Deploy with:
```bash
sudo cp /ganuda/scripts/systemd/jr-vetassist-worker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable jr-vetassist-worker
sudo systemctl start jr-vetassist-worker
```

---

## Verification Steps

1. **Check worker is running:**
   ```bash
   systemctl status jr-vetassist-worker
   journalctl -u jr-vetassist-worker -f
   ```

2. **Test research task:**
   ```bash
   curl -X POST http://192.168.132.223:8001/api/v1/research/trigger \
     -H "Content-Type: application/json" \
     -d '{"session_id": "test-123", "question": "Can veterans claim tinnitus?", "condition": "Hearing"}'
   ```

3. **Check result after 30-60 seconds:**
   ```bash
   curl http://192.168.132.223:8001/api/v1/research/results/test-123
   ```

4. **Verify report file created:**
   ```bash
   ls -la /ganuda/docs/research/RESEARCH-*
   ```

---

## Rollback Plan

If issues occur:
```bash
sudo systemctl stop jr-vetassist-worker
git checkout /ganuda/jr_executor/research_task_executor.py
```

---

## KB Article Reference

After completion, update: KB-JR-EXECUTOR-VETASSIST-RESEARCH-JAN27-2026

---

FOR SEVEN GENERATIONS
