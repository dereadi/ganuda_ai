#!/usr/bin/env python3
"""
Moltbook API Client — Cherokee AI Federation

Handles all HTTP communication with the Moltbook platform.
All requests go through this client; nothing else touches the external API.

Security: Crawdad-mandated constraints
- HTTPS only to moltbook.com
- 30-second timeouts
- No redirect following to non-moltbook domains
- No code execution from responses

Council Vote: 7/7 APPROVE (audit_hash: e804e3d63ae65981)
For Seven Generations
"""

import os
import re
import json
import hashlib
import logging
import requests
from datetime import datetime
from typing import Optional, Dict, List, Any
from urllib.parse import urlparse

logger = logging.getLogger('moltbook_proxy')

# Word to number mapping for CAPTCHA solving
WORD_TO_NUM = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
    'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
    'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
    'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17,
    'eighteen': 18, 'nineteen': 19, 'twenty': 20, 'thirty': 30,
    'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
    'eighty': 80, 'ninety': 90, 'hundred': 100,
}

MOLTBOOK_API_URL = os.environ.get('MOLTBOOK_API_URL', 'https://www.moltbook.com')
ALLOWED_DOMAINS = {'www.moltbook.com', 'moltbook.com'}
REQUEST_TIMEOUT = 30


class MoltbookClient:
    """Client for the Moltbook agent social network API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = MOLTBOOK_API_URL.rstrip('/') + '/api/v1'
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'CherokeeAIFederation/1.0'
        })
        # Disable automatic redirect following — we validate domains manually
        self.session.max_redirects = 0

    def _request(self, method: str, endpoint: str, data: dict = None) -> Dict:
        """Make a validated request to the Moltbook API."""
        url = f'{self.base_url}/{endpoint.lstrip("/")}'

        # Domain validation
        parsed = urlparse(url)
        if parsed.hostname not in ALLOWED_DOMAINS:
            raise ValueError(f'Blocked request to non-Moltbook domain: {parsed.hostname}')

        if parsed.scheme != 'https':
            raise ValueError(f'Blocked non-HTTPS request to {url}')

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=False
            )

            # If redirect, validate target domain before following
            if response.status_code in (301, 302, 303, 307, 308):
                redirect_url = response.headers.get('Location', '')
                redirect_parsed = urlparse(redirect_url)
                if redirect_parsed.hostname not in ALLOWED_DOMAINS:
                    logger.warning(f'Blocked redirect to {redirect_parsed.hostname}')
                    return {'error': f'Redirect to non-Moltbook domain blocked', 'status': response.status_code}
                # Follow the redirect manually
                response = self.session.request(
                    method=method,
                    url=redirect_url,
                    json=data,
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=False
                )

            result = {
                'status': response.status_code,
                'ok': response.ok,
            }

            try:
                result['data'] = response.json()
            except (json.JSONDecodeError, ValueError):
                result['data'] = {'raw': response.text[:2000]}

            return result

        except requests.exceptions.Timeout:
            logger.error(f'Timeout on {method} {endpoint}')
            return {'error': 'Request timed out', 'status': 0, 'ok': False}
        except requests.exceptions.ConnectionError as e:
            logger.error(f'Connection error on {method} {endpoint}: {e}')
            return {'error': str(e), 'status': 0, 'ok': False}

    # --- Agent Identity ---

    def register_agent(self, name: str, description: str, identity: dict = None) -> Dict:
        """Register the Federation agent on Moltbook."""
        payload = {
            'name': name,
            'description': description,
        }
        if identity:
            payload.update(identity)
        return self._request('POST', '/agents/register', payload)

    def get_profile(self) -> Dict:
        """Get our agent's profile."""
        return self._request('GET', '/agents/me')

    def update_profile(self, updates: dict) -> Dict:
        """Update our agent's profile."""
        return self._request('PATCH', '/agents/me', updates)

    # --- Submolts ---

    def create_submolt(self, name: str, display_name: str, description: str) -> Dict:
        """Create a submolt (community)."""
        return self._request('POST', '/submolts', {
            'name': name,
            'display_name': display_name,
            'description': description,
        })

    def get_submolt(self, name: str) -> Dict:
        """Get submolt info."""
        return self._request('GET', f'/submolts/{name}')

    # --- Posts ---

    def create_post(self, title: str, body: str, submolt: str = None) -> Dict:
        """Create a post."""
        payload = {'title': title, 'content': body}
        if submolt:
            payload['submolt'] = submolt
        return self._request('POST', '/posts', payload)

    def get_feed(self, sort: str = 'hot', limit: int = 25) -> Dict:
        """Get the main feed."""
        return self._request('GET', f'/posts?sort={sort}&limit={limit}')

    def get_post(self, post_id: str) -> Dict:
        """Get a single post."""
        return self._request('GET', f'/posts/{post_id}')

    # --- Comments ---

    def create_comment(self, post_id: str, body: str, parent_id: str = None) -> Dict:
        """
        Comment on a post, optionally as a nested reply to another comment.

        Args:
            post_id: UUID of the post
            body: Comment text
            parent_id: UUID of parent comment for nested/threaded replies (optional)
        """
        payload = {'content': body}
        if parent_id:
            payload['parent_id'] = parent_id
        return self._request('POST', f'/posts/{post_id}/comments', payload)

    def get_comments(self, post_id: str, sort: str = 'top') -> Dict:
        """Get comments on a post."""
        return self._request('GET', f'/posts/{post_id}/comments?sort={sort}')

    # --- Voting ---

    def upvote_post(self, post_id: str) -> Dict:
        """Upvote a post."""
        return self._request('POST', f'/posts/{post_id}/upvote')

    # --- Search ---

    def search(self, query: str) -> Dict:
        """Search posts, agents, communities."""
        return self._request('GET', f'/search?q={query}')

    # --- Social ---

    def follow_agent(self, agent_name: str) -> Dict:
        """Follow another agent."""
        return self._request('POST', f'/agents/{agent_name}/follow')

    def get_agent_profile(self, agent_name: str) -> Dict:
        """View another agent's profile."""
        return self._request('GET', f'/agents/profile?name={agent_name}')

    # --- Verification (CAPTCHA) ---

    def solve_captcha(self, challenge: str) -> str:
        """
        Solve Moltbook's math CAPTCHA challenge.

        Challenges are obfuscated text like:
        "A] Lo-BsT eR] ClAw^ ExErTs/ ThIrTy] FiVe~ NeOoToNs..."

        Returns the answer as a string with 2 decimal places (e.g., "57.00")
        """
        # Clean up the obfuscated text
        # Remove punctuation and normalize
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', challenge)
        cleaned = ' '.join(cleaned.lower().split())

        # Extract numbers (both digits and words)
        numbers = []

        # Find digit numbers
        for match in re.finditer(r'\b(\d+(?:\.\d+)?)\b', cleaned):
            numbers.append(float(match.group(1)))

        # Find word numbers
        words = cleaned.split()
        i = 0
        while i < len(words):
            word = words[i]
            if word in WORD_TO_NUM:
                num = WORD_TO_NUM[word]
                # Handle compounds like "thirty five" = 35
                if i + 1 < len(words) and words[i + 1] in WORD_TO_NUM:
                    next_num = WORD_TO_NUM[words[i + 1]]
                    if num >= 20 and next_num < 10:
                        num = num + next_num
                        i += 1
                numbers.append(float(num))
            i += 1

        if not numbers:
            logger.warning(f'No numbers found in CAPTCHA: {challenge[:100]}')
            return "0.00"

        # Determine operation from keywords
        cleaned_lower = cleaned.lower()
        if 'total' in cleaned_lower or 'sum' in cleaned_lower or 'add' in cleaned_lower or 'combined' in cleaned_lower:
            result = sum(numbers)
        elif 'difference' in cleaned_lower or 'subtract' in cleaned_lower or 'minus' in cleaned_lower or 'slow' in cleaned_lower or 'decreas' in cleaned_lower or 'reduc' in cleaned_lower or 'less' in cleaned_lower or 'fewer' in cleaned_lower:
            result = numbers[0] - sum(numbers[1:]) if len(numbers) > 1 else numbers[0]
        elif 'product' in cleaned_lower or 'multiply' in cleaned_lower or 'times' in cleaned_lower:
            result = 1
            for n in numbers:
                result *= n
        elif 'divide' in cleaned_lower or 'quotient' in cleaned_lower:
            result = numbers[0]
            for n in numbers[1:]:
                if n != 0:
                    result /= n
        else:
            # Default to sum for "what is X and Y" type questions
            result = sum(numbers)

        answer = f"{result:.2f}"
        logger.info(f'CAPTCHA challenge: {challenge[:100]}...')
        logger.info(f'CAPTCHA solved: {numbers} -> {answer}')
        return answer

    def verify_comment(self, verification_code: str, answer: str) -> Dict:
        """
        Submit CAPTCHA answer to verify a pending comment.

        Args:
            verification_code: The code from the verification response
            answer: The solved CAPTCHA answer (e.g., "57.00")
        """
        return self._request('POST', '/verify', {
            'verification_code': verification_code,
            'answer': answer
        })

    def create_comment_with_verification(self, post_id: str, body: str, parent_id: str = None) -> Dict:
        """
        Create a comment and automatically solve verification if required.

        Returns the final result after verification (if needed).
        """
        # Create the comment
        result = self.create_comment(post_id, body, parent_id)

        if not result.get('ok'):
            return result

        data = result.get('data', {})

        # Check if verification is required
        if data.get('verification_required') and data.get('verification'):
            verification = data['verification']
            challenge = verification.get('challenge', '')
            code = verification.get('code', '')

            if challenge and code:
                logger.info(f'Verification required, solving CAPTCHA...')
                answer = self.solve_captcha(challenge)
                verify_result = self.verify_comment(code, answer)

                if verify_result.get('ok'):
                    logger.info(f'Verification successful')
                    # Merge verification result into response
                    result['verification_result'] = verify_result.get('data', {})
                    result['verified'] = True
                else:
                    logger.warning(f'Verification failed: {verify_result}')
                    result['verification_result'] = verify_result
                    result['verified'] = False

        return result
