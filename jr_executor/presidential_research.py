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