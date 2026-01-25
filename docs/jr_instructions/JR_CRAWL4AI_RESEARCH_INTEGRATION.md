# Jr Instructions: Crawl4AI Web Research Integration

**Priority**: 1 (Enables Presidential Study)
**Assigned Jr**: it_triad_jr
**Prerequisite For**: Presidential Behavior Study

---

## OBJECTIVE

Integrate Crawl4AI into the Jr executor to enable web research capabilities. This will allow Jrs to fetch and analyze web content for research tasks.

---

### Task 1: Create Web Research Module

Create `/ganuda/jr_executor/web_research.py`:

```python
#!/usr/bin/env python3
"""
Web Research Module for Jr Agents
Uses Crawl4AI for web scraping and content extraction
Cherokee AI Federation - For Seven Generations
"""

import asyncio
from crawl4ai import AsyncWebCrawler
from typing import Optional, Dict, List
import json


async def fetch_url(url: str, extract_text: bool = True) -> Dict:
    """
    Fetch content from a URL using Crawl4AI.
    
    Args:
        url: The URL to fetch
        extract_text: If True, return markdown text; if False, return raw HTML
    
    Returns:
        Dict with 'success', 'content', 'url', and 'error' keys
    """
    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            return {
                'success': True,
                'url': url,
                'content': result.markdown if extract_text else result.html,
                'length': len(result.markdown),
                'error': None
            }
    except Exception as e:
        return {
            'success': False,
            'url': url,
            'content': None,
            'length': 0,
            'error': str(e)
        }


async def research_topic(topic: str, sources: List[str] = None) -> Dict:
    """
    Research a topic by fetching multiple sources.
    
    Args:
        topic: The topic to research
        sources: List of URLs to fetch (if None, uses Wikipedia)
    
    Returns:
        Dict with research results from all sources
    """
    if sources is None:
        # Default to Wikipedia
        wiki_topic = topic.replace(' ', '_')
        sources = [f"https://en.wikipedia.org/wiki/{wiki_topic}"]
    
    results = []
    for url in sources:
        result = await fetch_url(url)
        results.append(result)
    
    return {
        'topic': topic,
        'sources_fetched': len(results),
        'successful': sum(1 for r in results if r['success']),
        'results': results
    }


def sync_fetch_url(url: str) -> Dict:
    """Synchronous wrapper for fetch_url."""
    return asyncio.run(fetch_url(url))


def sync_research_topic(topic: str, sources: List[str] = None) -> Dict:
    """Synchronous wrapper for research_topic."""
    return asyncio.run(research_topic(topic, sources))


if __name__ == '__main__':
    # Test the module
    import sys
    if len(sys.argv) > 1:
        url = sys.argv[1]
        result = sync_fetch_url(url)
        print(f"Success: {result['success']}")
        print(f"Length: {result['length']} chars")
        if result['content']:
            print(f"Preview: {result['content'][:500]}...")
    else:
        print("Usage: python web_research.py <url>")
```

---

### Task 2: Create Presidential Research Script

Create `/ganuda/jr_executor/presidential_research.py`:

```python
#!/usr/bin/env python3
"""
Presidential Behavior Research Script
Fetches and analyzes data for all 46 US Presidents
Cherokee AI Federation - For Seven Generations
"""

import asyncio
import json
import os
from web_research import fetch_url
from datetime import datetime

PRESIDENTS = [
    (1, "George Washington", "1789-1797"),
    (2, "John Adams", "1797-1801"),
    (3, "Thomas Jefferson", "1801-1809"),
    (4, "James Madison", "1809-1817"),
    (5, "James Monroe", "1817-1825"),
    (6, "John Quincy Adams", "1825-1829"),
    (7, "Andrew Jackson", "1829-1837"),
    (8, "Martin Van Buren", "1837-1841"),
    (9, "William Henry Harrison", "1841"),
    (10, "John Tyler", "1841-1845"),
    (11, "James K. Polk", "1845-1849"),
    (12, "Zachary Taylor", "1849-1850"),
    (13, "Millard Fillmore", "1850-1853"),
    (14, "Franklin Pierce", "1853-1857"),
    (15, "James Buchanan", "1857-1861"),
    (16, "Abraham Lincoln", "1861-1865"),
    (17, "Andrew Johnson", "1865-1869"),
    (18, "Ulysses S. Grant", "1869-1877"),
    (19, "Rutherford B. Hayes", "1877-1881"),
    (20, "James A. Garfield", "1881"),
    (21, "Chester A. Arthur", "1881-1885"),
    (22, "Grover Cleveland", "1885-1889"),
    (23, "Benjamin Harrison", "1889-1893"),
    (24, "Grover Cleveland", "1893-1897"),
    (25, "William McKinley", "1897-1901"),
    (26, "Theodore Roosevelt", "1901-1909"),
    (27, "William Howard Taft", "1909-1913"),
    (28, "Woodrow Wilson", "1913-1921"),
    (29, "Warren G. Harding", "1921-1923"),
    (30, "Calvin Coolidge", "1923-1929"),
    (31, "Herbert Hoover", "1929-1933"),
    (32, "Franklin D. Roosevelt", "1933-1945"),
    (33, "Harry S. Truman", "1945-1953"),
    (34, "Dwight D. Eisenhower", "1953-1961"),
    (35, "John F. Kennedy", "1961-1963"),
    (36, "Lyndon B. Johnson", "1963-1969"),
    (37, "Richard Nixon", "1969-1974"),
    (38, "Gerald Ford", "1974-1977"),
    (39, "Jimmy Carter", "1977-1981"),
    (40, "Ronald Reagan", "1981-1989"),
    (41, "George H. W. Bush", "1989-1993"),
    (42, "Bill Clinton", "1993-2001"),
    (43, "George W. Bush", "2001-2009"),
    (44, "Barack Obama", "2009-2017"),
    (45, "Donald Trump", "2017-2021"),
    (46, "Joe Biden", "2021-2025"),
]

OUTPUT_DIR = "/ganuda/data/presidential_study"


async def fetch_president_data(number: int, name: str, term: str) -> dict:
    """Fetch Wikipedia data for a president."""
    wiki_name = name.replace(' ', '_')
    url = f"https://en.wikipedia.org/wiki/{wiki_name}"
    
    print(f"[{number}/46] Fetching {name}...")
    result = await fetch_url(url)
    
    return {
        'number': number,
        'name': name,
        'term': term,
        'url': url,
        'success': result['success'],
        'content_length': result['length'],
        'content': result['content'][:50000] if result['content'] else None,  # Limit size
        'error': result['error']
    }


async def research_all_presidents():
    """Fetch data for all 46 presidents."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    results = []
    for num, name, term in PRESIDENTS:
        result = await fetch_president_data(num, name, term)
        results.append(result)
        
        # Save individual file
        filename = f"{OUTPUT_DIR}/president_{num:02d}_{name.replace(' ', '_')}.json"
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
    
    # Save summary
    summary = {
        'generated_at': datetime.now().isoformat(),
        'total_presidents': len(results),
        'successful_fetches': sum(1 for r in results if r['success']),
        'presidents': [
            {
                'number': r['number'],
                'name': r['name'],
                'term': r['term'],
                'success': r['success'],
                'content_length': r['content_length']
            }
            for r in results
        ]
    }
    
    with open(f"{OUTPUT_DIR}/research_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nResearch complete!")
    print(f"  Successful: {summary['successful_fetches']}/46")
    print(f"  Output: {OUTPUT_DIR}/")
    
    return summary


if __name__ == '__main__':
    asyncio.run(research_all_presidents())
```

---

### Task 3: Test Web Research

Run the test to verify crawl4ai works:

```bash
cd /ganuda/jr_executor
source /home/dereadi/cherokee_venv/bin/activate
python3 web_research.py "https://en.wikipedia.org/wiki/Abraham_Lincoln"
```

---

### Task 4: Run Presidential Research

Execute the full presidential research:

```bash
cd /ganuda/jr_executor
source /home/dereadi/cherokee_venv/bin/activate
python3 presidential_research.py
```

---

## SUCCESS CRITERIA

1. web_research.py module created and working
2. presidential_research.py fetches all 46 presidents
3. JSON files created in /ganuda/data/presidential_study/
4. research_summary.json shows 46/46 successful

---

*For Seven Generations - Cherokee AI Federation*
