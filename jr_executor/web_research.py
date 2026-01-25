import requests
from bs4 import BeautifulSoup
import markdownify
import asyncio
import aiohttp

def fetch_url(url):
    """Fetches the content from a given URL and converts it to markdown."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        markdown_content = markdownify.markdownify(str(soup))
        return markdown_content
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

async def fetch_url_async(session, url):
    """Asynchronously fetches the content from a given URL and converts it to markdown."""
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            html_content = await response.text()
            soup = BeautifulSoup(html_content, 'html.parser')
            markdown_content = markdownify.markdownify(str(soup))
            return markdown_content
    except aiohttp.ClientError as e:
        print(f"Error fetching {url}: {e}")
        return None

async def research_topic(topic, sources):
    """Asynchronously fetches content from multiple URLs related to a topic."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url_async(session, url) for url in sources]
        results = await asyncio.gather(*tasks)
        return results

def sync_fetch_url(url):
    """Synchronous wrapper for fetch_url(url)."""
    return fetch_url(url)

def sync_research_topic(topic, sources):
    """Synchronous wrapper for research_topic(topic, sources)."""
    return [fetch_url(url) for url in sources]
