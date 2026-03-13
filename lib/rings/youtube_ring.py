#!/usr/bin/env python3
"""YouTube Ring — Fetch video transcripts and metadata via the chain protocol."""

import json
import os
import re
import subprocess
import sys

sys.path.insert(0, "/ganuda/lib")
from web_ring import WebRing


class YouTubeRing(WebRing):
    """YouTube web service ring.

    Passive mode: fetch transcript + metadata for a specific video URL.
    Active mode: search YouTube for videos matching a query.

    Uses yt-dlp for transcript extraction (no API key needed for public videos).
    Uses YouTube Data API v3 for search (requires API key).
    """

    ring_name = "youtube"
    ring_type = "temp"
    modes = ["passive", "active"]

    # YouTube API quota: 10,000 units/day (free tier)
    # Search: 100 units. Video details: 1 unit. Captions: ~50 units.
    DAILY_QUOTA_UNITS = 10000

    def fetch(self, url: str) -> dict:
        """Fetch transcript and metadata for a YouTube video URL."""
        video_id = self._extract_video_id(url)
        if not video_id:
            return {"error": f"Could not extract video ID from: {url}"}

        result = {"video_id": video_id, "url": url}

        # Get metadata + transcript via yt-dlp (no API key needed)
        try:
            meta = subprocess.run(
                ["yt-dlp", "--dump-json", "--skip-download", url],
                capture_output=True, text=True, timeout=30
            )
            if meta.returncode == 0:
                data = json.loads(meta.stdout)
                result["title"] = data.get("title", "")
                result["channel"] = data.get("channel", "")
                result["duration"] = data.get("duration", 0)
                result["upload_date"] = data.get("upload_date", "")
                result["view_count"] = data.get("view_count", 0)
                result["description"] = data.get("description", "")[:500]
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
            result["metadata_error"] = str(e)

        # Get transcript via yt-dlp subtitle extraction
        try:
            transcript = subprocess.run(
                ["yt-dlp", "--write-auto-sub", "--sub-lang", "en",
                 "--skip-download", "--sub-format", "vtt",
                 "-o", "/tmp/yt_transcript_%(id)s",
                 url],
                capture_output=True, text=True, timeout=60
            )
            vtt_path = f"/tmp/yt_transcript_{video_id}.en.vtt"
            if os.path.exists(vtt_path):
                with open(vtt_path) as f:
                    raw_vtt = f.read()
                result["content"] = self._clean_vtt(raw_vtt)
                result["has_transcript"] = True
                os.remove(vtt_path)
            else:
                result["content"] = ""
                result["has_transcript"] = False
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            result["content"] = ""
            result["has_transcript"] = False
            result["transcript_error"] = str(e)

        return result

    def search(self, query: str) -> dict:
        """Search YouTube for videos. Requires YOUTUBE_API_KEY in secrets.env."""
        import requests

        api_key = os.environ.get("YOUTUBE_API_KEY", "")
        if not api_key:
            return {"error": "YOUTUBE_API_KEY not configured"}

        resp = requests.get("https://www.googleapis.com/youtube/v3/search", params={
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": 5,
            "key": api_key,
        }, timeout=15)

        if resp.status_code != 200:
            return {"error": f"YouTube API error: {resp.status_code}", "detail": resp.text[:200]}

        data = resp.json()
        results = []
        for item in data.get("items", []):
            results.append({
                "video_id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "published": item["snippet"]["publishedAt"],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
            })

        return {"results": results, "query": query, "count": len(results)}

    def calibrate(self) -> dict:
        """Calibration: fetch a known video and verify transcript extraction."""
        # Rick Astley — known stable, always has transcripts
        result = self.fetch("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        expected_title_fragment = "Rick Astley"
        has_title = expected_title_fragment.lower() in result.get("title", "").lower()
        has_transcript = result.get("has_transcript", False)
        drift = 0.0 if (has_title and has_transcript) else 0.5
        return {"status": "pass" if drift == 0.0 else "degraded",
                "drift": drift, "checks": {"title": has_title, "transcript": has_transcript}}

    def health_check(self) -> bool:
        """Can we reach YouTube at all?"""
        import requests
        try:
            resp = requests.head("https://www.youtube.com", timeout=5)
            return resp.status_code < 500
        except Exception:
            return False

    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from various YouTube URL formats."""
        patterns = [
            r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})",
            r"^([a-zA-Z0-9_-]{11})$",
        ]
        for p in patterns:
            m = re.search(p, url)
            if m:
                return m.group(1)
        return ""

    def _clean_vtt(self, vtt_text: str) -> str:
        """Clean VTT subtitle format into plain text."""
        lines = []
        for line in vtt_text.split("\n"):
            # Skip timestamps and headers
            if "-->" in line or line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
                continue
            line = re.sub(r"<[^>]+>", "", line).strip()
            if line and line not in lines[-1:]:
                lines.append(line)
        return " ".join(lines)