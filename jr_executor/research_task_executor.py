#!/usr/bin/env python3
"""
Research Task Executor - Handles web research tasks for Research Jr.

Uses Crawl4AI to fetch academic papers and web content,
then uses local LLM for analysis and summarization.

Cherokee AI Federation - For Seven Generations
Created: January 22, 2026
"""

import json
import os
import re
import hashlib
from typing import Dict, List, Optional
from datetime import datetime

from web_research import sync_fetch_url, sync_research_topic


class ResearchTaskExecutor:
    """Executes research tasks with web access via Crawl4AI."""

    def __init__(self):
        self.output_dir = "/ganuda/docs/research"
        os.makedirs(self.output_dir, exist_ok=True)

    def execute_research_task(self, task: Dict) -> Dict:
        """
        Execute a research task.

        Args:
            task: Task dict with 'title', 'instructions', 'parameters'

        Returns:
            Result dict with 'success', 'artifacts', 'summary', 'steps_executed'
        """
        title = task.get('title', 'Unknown Research Task')
        instructions = task.get('instructions', '')
        params = task.get('parameters', {})

        print(f"[ResearchTaskExecutor] Starting: {title}")

        # Extract URLs and topics from instructions
        urls = self._extract_urls(instructions)
        topics = self._extract_topics(instructions)
        arxiv_ids = self._extract_arxiv_ids(instructions)

        print(f"[ResearchTaskExecutor] Found {len(urls)} URLs, {len(topics)} topics, {len(arxiv_ids)} ArXiv IDs")

        results = []
        artifacts = []
        steps_executed = []

        # Fetch ArXiv papers by ID
        for arxiv_id in arxiv_ids:
            url = f"https://arxiv.org/abs/{arxiv_id}"
            if url not in urls:
                urls.append(url)

        # Fetch specified URLs
        for url in urls:
            print(f"[ResearchTaskExecutor] Fetching: {url}")
            try:
                raw_result = sync_fetch_url(url)

                # Handle different return types from web_research.py
                # It may return: string (content), None (error), or dict (full result)
                if raw_result is None:
                    result = {'success': False, 'error': 'No result returned', 'length': 0, 'content': None}
                elif isinstance(raw_result, str):
                    # String means successful fetch, content is the string
                    result = {'success': True, 'content': raw_result, 'length': len(raw_result), 'error': None}
                elif isinstance(raw_result, dict):
                    result = raw_result
                else:
                    result = {'success': False, 'error': f'Unexpected result type: {type(raw_result)}', 'length': 0, 'content': None}
            except Exception as e:
                print(f"[ResearchTaskExecutor] Fetch error: {e}")
                result = {'success': False, 'error': str(e), 'length': 0, 'content': None}

            results.append(result)

            step = {
                'type': 'fetch_url',
                'url': url,
                'success': result.get('success', False),
                'length': result.get('length', 0)
            }
            steps_executed.append(step)

            if result.get('success') and result.get('content'):
                # Save fetched content
                filename = self._save_content(url, result['content'])
                artifacts.append({
                    'type': 'fetched_content',
                    'url': url,
                    'path': filename,
                    'length': result.get('length', len(result['content']))
                })
                print(f"[ResearchTaskExecutor] Saved: {filename}")
            else:
                print(f"[ResearchTaskExecutor] Failed: {url} - {result.get('error', 'Unknown error')}")

        # Research topics (Wikipedia fallback)
        for topic in topics:
            print(f"[ResearchTaskExecutor] Researching topic: {topic}")
            # Generate Wikipedia URL from topic
            wiki_topic = topic.replace(' ', '_').replace('(', '').replace(')', '')
            wiki_url = f"https://en.wikipedia.org/wiki/{wiki_topic}"

            try:
                topic_results = sync_research_topic(topic, [wiki_url])
                # sync_research_topic returns a list of results
                successful = sum(1 for r in topic_results if r is not None)
                result = {
                    'topic': topic,
                    'sources': [wiki_url],
                    'successful': successful,
                    'sources_fetched': len(topic_results),
                    'content': topic_results[0] if topic_results and topic_results[0] else None
                }
            except Exception as e:
                print(f"[ResearchTaskExecutor] Topic research error: {e}")
                result = {'topic': topic, 'successful': 0, 'sources_fetched': 0, 'error': str(e)}

            results.append(result)

            step = {
                'type': 'research_topic',
                'topic': topic,
                'success': result.get('successful', 0) > 0,
                'sources_fetched': result.get('sources_fetched', 0)
            }
            steps_executed.append(step)

        # Generate summary report
        summary_content = self._generate_summary(title, results, instructions)
        safe_title = re.sub(r'[^\w\s-]', '', title)[:40].replace(' ', '-')
        summary_file = f"{self.output_dir}/RESEARCH-{safe_title}-{datetime.now().strftime('%Y%m%d-%H%M')}.md"

        with open(summary_file, 'w') as f:
            f.write(summary_content)

        artifacts.append({
            'type': 'research_summary',
            'path': summary_file
        })

        steps_executed.append({
            'type': 'generate_summary',
            'path': summary_file,
            'success': True
        })

        successful_fetches = sum(1 for r in results if r.get('success'))
        total_fetches = len(results)

        return {
            'success': successful_fetches > 0 or len(topics) > 0,
            'artifacts': artifacts,
            'steps_executed': steps_executed,
            'summary': f"Fetched {successful_fetches}/{total_fetches} sources. Report: {summary_file}",
            'sources_fetched': total_fetches,
            'successful_fetches': successful_fetches
        }

    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs from instruction text, filtering out internal IPs."""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]\)\,]+'
        urls = list(set(re.findall(url_pattern, text)))
        # Clean trailing punctuation
        urls = [url.rstrip('.,;:') for url in urls]

        # Filter out internal/private IP addresses (not meant to be fetched)
        filtered = []
        for url in urls:
            # Skip internal IPs (192.168.x.x, 10.x.x.x, 172.16-31.x.x, localhost)
            if any(ip in url for ip in ['192.168.', '10.', '172.16.', '172.17.', '172.18.', '172.19.',
                                         '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.',
                                         '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.',
                                         'localhost', '127.0.0.1']):
                print(f"[ResearchTaskExecutor] Skipping internal URL: {url}")
                continue
            filtered.append(url)

        return filtered

    def _extract_arxiv_ids(self, text: str) -> List[str]:
        """Extract ArXiv paper IDs (e.g., 2401.00001)."""
        arxiv_pattern = r'\b(\d{4}\.\d{4,5})\b'
        return list(set(re.findall(arxiv_pattern, text)))

    def _extract_topics(self, text: str) -> List[str]:
        """Extract research topics from instruction text."""
        patterns = [
            r'Paper \d+:\s*([^\n]+)',
            r'Research:\s*([^\n]+)',
            r'Topic:\s*([^\n]+)',
            r'Analyze:\s*([^\n]+)',
        ]
        topics = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            topics.extend(matches)
        return topics

    def _save_content(self, url: str, content: str) -> str:
        """Save fetched content to file."""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]

        # Determine file type from URL
        if 'arxiv.org' in url:
            prefix = 'arxiv'
        elif 'semanticscholar.org' in url:
            prefix = 'semscholar'
        elif 'wikipedia.org' in url:
            prefix = 'wiki'
        else:
            prefix = 'web'

        filename = f"{self.output_dir}/fetched_{prefix}_{url_hash}.md"

        with open(filename, 'w') as f:
            f.write(f"# Source: {url}\n")
            f.write(f"# Fetched: {datetime.now().isoformat()}\n\n")
            f.write(content)

        return filename

    def _generate_summary(self, title: str, results: List[Dict], instructions: str) -> str:
        """Generate a markdown summary of research results."""
        successful = sum(1 for r in results if r.get('success'))
        total = len(results)

        summary = f"""# Research Summary: {title}

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Sources Attempted:** {total}
**Sources Fetched:** {successful}

## Original Instructions

{instructions[:2000]}{'...' if len(instructions) > 2000 else ''}

## Sources Retrieved

"""
        for i, result in enumerate(results, 1):
            if 'url' in result:
                status = "+" if result.get('success') else "x"
                length = result.get('length', 0)
                summary += f"{i}. [{status}] {result['url']} ({length:,} chars)\n"
            elif 'topic' in result:
                fetched = result.get('successful', 0)
                total_topic = result.get('sources_fetched', 0)
                summary += f"{i}. [Topic] {result['topic']} ({fetched}/{total_topic} sources)\n"

        summary += """
## Next Steps

- Analyze fetched content for key insights
- Extract relevant findings for Cherokee AI architecture
- Update KB articles with discoveries

## For Seven Generations

This research contributes to the Cherokee AI Federation's knowledge base,
building wisdom that will guide future generations of AI development.
"""
        return summary


def is_research_task(task: Dict, instructions: str) -> bool:
    """
    Determine if a task should use the ResearchTaskExecutor.

    Returns True if:
    - Task has 'research' in tags
    - Task title contains 'research'
    - Instructions contain ArXiv/Semantic Scholar URLs
    - Task assigned to 'Research Jr.'
    """
    tags = task.get('tags', []) or []
    title = task.get('title', '').lower()
    assigned_jr = task.get('assigned_jr', '').lower()
    instructions_lower = instructions.lower()

    # Check tags
    if 'research' in [t.lower() for t in tags]:
        return True

    # Check title
    if 'research' in title:
        return True

    # Check assigned Jr
    if 'research jr' in assigned_jr:
        return True

    # Check for academic URLs in instructions
    academic_indicators = [
        'arxiv.org',
        'semanticscholar.org',
        'scholar.google.com',
        'paper analysis',
        'pull the paper',
        'fetch the paper'
    ]
    for indicator in academic_indicators:
        if indicator in instructions_lower:
            return True

    return False


if __name__ == '__main__':
    # Test the executor
    executor = ResearchTaskExecutor()
    test_task = {
        'title': 'Test ArXiv Fetch',
        'instructions': '''
        Fetch and analyze this ArXiv paper: https://arxiv.org/abs/2401.00001

        Focus on:
        - Key findings
        - Methodology
        - Relevance to our architecture
        ''',
        'parameters': {}
    }
    result = executor.execute_research_task(test_task)
    print(json.dumps(result, indent=2))
