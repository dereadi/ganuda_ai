"""Council Web Research Tool.
Provides web search and page extraction for council specialists.
No API key required — uses DuckDuckGo search."""

import time
import hashlib
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

_cache = {}
_CACHE_TTL = 300
_LAST_REQUEST = 0
_RATE_LIMIT = 2.0

def _rate_limit():
    global _LAST_REQUEST
    elapsed = time.time() - _LAST_REQUEST
    if elapsed < _RATE_LIMIT:
        time.sleep(_RATE_LIMIT - elapsed)
    _LAST_REQUEST = time.time()

def _cache_key(query):
    return hashlib.sha256(query.encode()).hexdigest()

def _get_cached(key):
    if key in _cache:
        entry = _cache[key]
        if datetime.now() - entry["time"] < timedelta(seconds=_CACHE_TTL):
            return entry["data"]
        del _cache[key]
    return None

def _set_cached(key, data):
    _cache[key] = {"data": data, "time": datetime.now()}
    if len(_cache) > 100:
        oldest = min(_cache, key=lambda k: _cache[k]["time"])
        del _cache[oldest]

def search_web(query, max_results=5):
    """Search the web using DuckDuckGo HTML. Returns list of {title, url, snippet}."""
    key = _cache_key(f"search:{query}")
    cached = _get_cached(key)
    if cached:
        return cached
    _rate_limit()
    try:
        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Cherokee-AI-Federation/1.0"},
            timeout=10
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for r in soup.select(".result")[:max_results]:
            title_el = r.select_one(".result__title a")
            snippet_el = r.select_one(".result__snippet")
            if title_el:
                results.append({
                    "title": title_el.get_text(strip=True),
                    "url": title_el.get("href", ""),
                    "snippet": snippet_el.get_text(strip=True) if snippet_el else ""
                })
        _set_cached(key, results)
        return results
    except Exception as e:
        return [{"title": "Error", "url": "", "snippet": str(e)}]

def fetch_page_text(url, max_chars=5000):
    """Fetch and extract text from a web page."""
    key = _cache_key(f"page:{url}")
    cached = _get_cached(key)
    if cached:
        return cached
    _rate_limit()
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Cherokee-AI-Federation/1.0"},
            timeout=15
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)[:max_chars]
        _set_cached(key, text)
        return text
    except Exception as e:
        return f"Error fetching {url}: {e}"