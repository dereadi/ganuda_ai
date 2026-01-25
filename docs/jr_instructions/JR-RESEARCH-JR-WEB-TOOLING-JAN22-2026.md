# JR: Wire Research Jr with Web Access Capabilities

**Date:** January 22, 2026
**Priority:** High
**Type:** Infrastructure Integration
**Assigned To:** Infrastructure Jr

## Objective

Create and register a "Research Jr" with web access capabilities using the existing Crawl4AI web_research.py module. This Jr will handle research tasks that require fetching content from ArXiv, Semantic Scholar, Wikipedia, and other sources.

## Background

The web research module already exists at `/ganuda/jr_executor/web_research.py` providing:
- `fetch_url(url)` - Fetch and convert web content to markdown
- `research_topic(topic, sources)` - Multi-source research
- `sync_fetch_url()` / `sync_research_topic()` - Synchronous wrappers

Task #261 (Flat Earth AI Research) failed because the Software Engineer Jr doesn't have web access.

## Implementation Steps

### Step 1: Register Research Jr in Database

```sql
-- Add Research Jr to jr_status
INSERT INTO jr_status (
    jr_name,
    jr_mountain,
    jr_gender,
    jr_model,
    jr_role,
    endpoint,
    is_online,
    specialties
) VALUES (
    'Research Jr.',
    'Lookout',
    'non-binary',
    'qwen2.5-coder-32b-awq',
    'Web research specialist with Crawl4AI integration. Authorized to fetch content from ArXiv, Semantic Scholar, Wikipedia, and academic sources. Analyzes papers and produces summaries.',
    'http://192.168.132.223:8000',
    true,
    ARRAY['web research', 'paper analysis', 'crawl4ai', 'academic sources', 'ArXiv', 'Semantic Scholar']
) ON CONFLICT (jr_name) DO UPDATE SET
    specialties = EXCLUDED.specialties,
    jr_role = EXCLUDED.jr_role,
    is_online = true,
    updated_at = NOW();
```

### Step 2: Create Research Task Executor

Create `/ganuda/jr_executor/research_task_executor.py`:

```python
#!/usr/bin/env python3
"""
Research Task Executor - Handles web research tasks for Research Jr.

Uses Crawl4AI to fetch academic papers and web content,
then uses local LLM for analysis and summarization.

Cherokee AI Federation - For Seven Generations
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime

from web_research import sync_fetch_url, sync_research_topic

# ArXiv search URLs
ARXIV_SEARCH_URL = "https://arxiv.org/search/?query={query}&searchtype=all"
ARXIV_ABS_URL = "https://arxiv.org/abs/{paper_id}"

# Semantic Scholar API
SEMANTIC_SCHOLAR_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit=5"


class ResearchTaskExecutor:
    """Executes research tasks with web access."""

    def __init__(self):
        self.output_dir = "/ganuda/docs/research"
        os.makedirs(self.output_dir, exist_ok=True)

    def execute_research_task(self, task: Dict) -> Dict:
        """
        Execute a research task.

        Args:
            task: Task dict with 'title', 'instructions', 'parameters'

        Returns:
            Result dict with 'success', 'artifacts', 'summary'
        """
        instructions = task.get('instructions', '')
        params = task.get('parameters', {})

        # Extract URLs/topics from instructions
        urls = self._extract_urls(instructions)
        topics = self._extract_topics(instructions)

        results = []
        artifacts = []

        # Fetch specified URLs
        for url in urls:
            result = sync_fetch_url(url)
            results.append(result)

            if result['success']:
                # Save fetched content
                filename = self._save_content(url, result['content'])
                artifacts.append({
                    'type': 'fetched_content',
                    'url': url,
                    'path': filename,
                    'length': result['length']
                })

        # Research topics
        for topic in topics:
            result = sync_research_topic(topic)
            results.append(result)

        # Generate summary report
        summary = self._generate_summary(task['title'], results)
        summary_file = f"{self.output_dir}/RESEARCH-{task['title'][:30].replace(' ', '-')}-{datetime.now().strftime('%Y%m%d')}.md"

        with open(summary_file, 'w') as f:
            f.write(summary)

        artifacts.append({
            'type': 'research_summary',
            'path': summary_file
        })

        return {
            'success': True,
            'artifacts': artifacts,
            'summary': f"Fetched {len(urls)} URLs, researched {len(topics)} topics",
            'sources_fetched': len(results)
        }

    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs from instruction text."""
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return list(set(re.findall(url_pattern, text)))

    def _extract_topics(self, text: str) -> List[str]:
        """Extract research topics from instruction text."""
        # Look for patterns like "Paper 1: Topic" or "Research: Topic"
        import re
        patterns = [
            r'Paper \d+:\s*([^\n]+)',
            r'Research:\s*([^\n]+)',
            r'Topic:\s*([^\n]+)',
        ]
        topics = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            topics.extend(matches)
        return topics

    def _save_content(self, url: str, content: str) -> str:
        """Save fetched content to file."""
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"{self.output_dir}/fetched_{url_hash}.md"
        with open(filename, 'w') as f:
            f.write(f"# Source: {url}\n\n{content}")
        return filename

    def _generate_summary(self, title: str, results: List[Dict]) -> str:
        """Generate a markdown summary of research results."""
        successful = sum(1 for r in results if r.get('success'))

        summary = f"""# Research Summary: {title}

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Sources Fetched:** {successful}/{len(results)}

## Sources

"""
        for i, result in enumerate(results, 1):
            if 'url' in result:
                status = "✅" if result.get('success') else "❌"
                summary += f"{i}. {status} {result['url']} ({result.get('length', 0)} chars)\n"

        summary += """
## For Seven Generations

This research contributes to the Cherokee AI Federation's knowledge base.
"""
        return summary


if __name__ == '__main__':
    # Test
    executor = ResearchTaskExecutor()
    test_task = {
        'title': 'Test Research',
        'instructions': 'Fetch https://arxiv.org/abs/2512.24601',
        'parameters': {}
    }
    result = executor.execute_research_task(test_task)
    print(json.dumps(result, indent=2))
```

### Step 3: Update Task Executor Router

In `/ganuda/jr_executor/task_executor.py`, add routing for research tasks:

```python
# Add to imports
from research_task_executor import ResearchTaskExecutor

# In process_queue_task method, add:
def process_queue_task(self, task: dict) -> dict:
    # Check if this is a research task
    tags = task.get('tags', [])
    title_lower = task.get('title', '').lower()

    if 'research' in tags or 'research' in title_lower:
        research_executor = ResearchTaskExecutor()
        return research_executor.execute_research_task(task)

    # ... existing RLM execution path
```

### Step 4: Create Research Jr Queue Worker

Create `/ganuda/jr_executor/research_jr_worker.py`:

```python
#!/usr/bin/env python3
"""
Research Jr Queue Worker - Specialized worker for web research tasks.

Uses Crawl4AI for web fetching and local LLM for analysis.

Cherokee AI Federation - For Seven Generations
"""

from jr_queue_worker import JrQueueWorker

if __name__ == "__main__":
    worker = JrQueueWorker("Research Jr.")
    worker.run()
```

### Step 5: Create systemd Service

Create `/ganuda/services/research-jr-worker.service`:

```ini
[Unit]
Description=Cherokee AI Research Jr Queue Worker
After=network.target postgresql.service

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/jr_executor
Environment="PATH=/home/dereadi/cherokee_venv/bin:/usr/bin"
ExecStart=/home/dereadi/cherokee_venv/bin/python3 jr_queue_worker.py "Research Jr."
Restart=on-failure
RestartSec=30

StandardOutput=append:/ganuda/logs/research_jr_worker.log
StandardError=append:/ganuda/logs/research_jr_worker.log

[Install]
WantedBy=multi-user.target
```

### Step 6: Reassign Task #261

```sql
-- Reassign Flat Earth AI Research to Research Jr
UPDATE jr_work_queue
SET
    assigned_jr = 'Research Jr.',
    status = 'assigned',
    status_message = NULL,
    assigned_at = NOW()
WHERE id = 261;
```

## Testing

```bash
# 1. Register Research Jr
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -f /ganuda/sql/register_research_jr.sql

# 2. Test web research module
cd /ganuda/jr_executor
source /home/dereadi/cherokee_venv/bin/activate
python3 web_research.py "https://arxiv.org/abs/2512.24601"

# 3. Start Research Jr worker
python3 jr_queue_worker.py "Research Jr."
```

## Success Criteria

- [ ] Research Jr registered in jr_status with web specialties
- [ ] research_task_executor.py created and working
- [ ] Task #261 reassigned to Research Jr
- [ ] Research Jr can fetch ArXiv papers
- [ ] Research summaries saved to /ganuda/docs/research/

## For Seven Generations

Web research capabilities expand the Federation's ability to learn from the broader world while maintaining our architectural principles of specialist isolation and explicit capability grants.
