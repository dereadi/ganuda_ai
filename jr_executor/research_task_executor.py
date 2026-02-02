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
import time

# Phase 10: LLM Reasoner for content synthesis
# Council vote 6428bcda34efc7f9 — approved with conditions
import sys
sys.path.insert(0, '/ganuda/lib')
try:
    from jr_llm_reasoner import get_reasoner_sync
    LLM_REASONER_AVAILABLE = True
except ImportError:
    LLM_REASONER_AVAILABLE = False
    print("[ResearchTaskExecutor] LLM Reasoner not available — synthesis disabled")

# VetAssist authoritative source URLs
# Maps source names from instructions to actual URLs for fetching
VETASSIST_SOURCE_URLS = {
    'va.gov': [
        'https://www.va.gov/disability/eligibility/',
        'https://www.va.gov/disability/how-to-file-claim/',
    ],
    '38cfr': [
        'https://www.ecfr.gov/current/title-38/chapter-I/part-3',
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
}

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

        # Extract VetAssist source URLs (maps source names to actual URLs)
        vetassist_urls = self._extract_vetassist_urls(instructions)
        urls.extend(vetassist_urls)

        print(f"[ResearchTaskExecutor] Found {len(urls)} URLs, {len(topics)} topics, {len(arxiv_ids)} ArXiv IDs, {len(vetassist_urls)} VetAssist sources")

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

            result['url'] = url  # Ensure URL available for summary generation
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

        # Council fallback when no sources fetched
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
                    council_synthesis = council_data.get('synthesis', council_data.get('final_answer', 'Council consulted'))

                    # Update summary with council response
                    summary_content += f"\n\n## Council Consultation\n\n{council_synthesis}\n"
                    with open(summary_file, 'w') as f:
                        f.write(summary_content)

                    artifacts.append({
                        'type': 'council_consultation',
                        'synthesis': council_synthesis[:500]
                    })
                    steps_executed.append({'type': 'council_fallback', 'success': True})

                    return {
                        'success': True,
                        'artifacts': artifacts,
                        'steps_executed': steps_executed,
                        'summary': f"Council consulted (no web sources). Report: {summary_file}",
                        'sources_fetched': 0,
                        'council_consulted': True
                    }
            except Exception as council_error:
                print(f"[ResearchTaskExecutor] Council fallback failed: {council_error}")

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

    def _extract_topics(self, text: str) -> List[str]:
        """Extract research topics from instruction text."""
        patterns = [
            r'Paper \d+:\s*([^\n]+)',
            r'Research:\s*([^\n]+)',
            r'Topic:\s*([^\n]+)',
            r'Analyze:\s*([^\n]+)',
            r'QUESTION:\s*([^\n]+)',  # VetAssist format
            r'Question:\s*([^\n]+)',  # Case variation
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
        """Generate a markdown summary of research results with LLM synthesis."""
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

        # Phase 10: LLM Synthesis of fetched content
        synthesis = self._synthesize_results(results, instructions)
        if synthesis:
            summary += f"\n## Key Findings\n\n{synthesis}\n"

        source_summaries = self._summarize_sources(results)
        if source_summaries:
            summary += f"\n## Source Summaries\n\n{source_summaries}\n"

        summary += """
## For Seven Generations

This research contributes to the Cherokee AI Federation's knowledge base,
building wisdom that will guide future generations of AI development.
"""
        return summary

    def _synthesize_results(self, results: List[Dict], instructions: str) -> str:
        """
        Phase 10: Synthesize fetched content using LLM reasoner.
        Council vote 6428bcda34efc7f9 — Crawdad: public content only, local LLM.
        Returns empty string on failure (graceful fallback).
        """
        if not LLM_REASONER_AVAILABLE:
            print("[SYNTHESIS] LLM not available — skipping synthesis")
            return ""

        successful_content = []
        for r in results:
            if r.get('success') and r.get('content'):
                truncated = r['content'][:6000]
                source_label = r.get('url', r.get('topic', 'Unknown source'))
                successful_content.append((source_label, truncated))

        if not successful_content:
            print("[SYNTHESIS] No content to synthesize")
            return ""

        try:
            start_time = time.time()
            reasoner = get_reasoner_sync()

            sources_text = ""
            for source, content in successful_content[:3]:
                sources_text += f"\n--- Source: {source} ---\n{content}\n"

            prompt = f"""You are a research analyst. Synthesize the following source content into key findings relevant to this research task.

RESEARCH TASK: {instructions[:500]}

SOURCES:
{sources_text}

Provide 3-5 key findings as bullet points. Be specific and cite which source each finding comes from. Focus on actionable insights."""

            synthesis = reasoner.simple_completion(prompt, max_tokens=2000)
            elapsed = time.time() - start_time
            print(f"[SYNTHESIS] Complete in {elapsed:.1f}s — {len(synthesis)} chars")
            return synthesis
        except Exception as e:
            print(f"[SYNTHESIS] Failed: {e}")
            return ""

    def _summarize_sources(self, results: List[Dict]) -> str:
        """
        Phase 10: Generate brief summaries of each fetched source.
        Returns empty string on failure (graceful fallback).
        """
        if not LLM_REASONER_AVAILABLE:
            return ""

        summaries = []
        try:
            reasoner = get_reasoner_sync()
            for r in results:
                if r.get('success') and r.get('content'):
                    source = r.get('url', r.get('topic', 'Unknown'))
                    content_preview = r['content'][:3000]

                    prompt = f"""Summarize this web content in 2-3 sentences. Focus on the main topic and key facts.

SOURCE: {source}
CONTENT:
{content_preview}

Summary:"""
                    try:
                        start_time = time.time()
                        summary = reasoner.simple_completion(prompt, max_tokens=300)
                        elapsed = time.time() - start_time
                        summaries.append(f"**{source}**: {summary.strip()}")
                        print(f"[SYNTHESIS] Source summary for {source} in {elapsed:.1f}s")
                    except Exception:
                        summaries.append(f"**{source}**: Content fetched ({r.get('length', 0):,} chars) — summary unavailable")
        except Exception as e:
            print(f"[SYNTHESIS] Source summarization failed: {e}")
            return ""

        return "\n\n".join(summaries)


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
