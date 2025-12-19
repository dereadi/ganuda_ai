#!/usr/bin/env python3
"""
Code Detection and Extraction Helpers for Cherokee Chief Telegram Bot
"""

import re
from datetime import datetime


def detect_code_request(text: str) -> dict:
    """Detect if user is asking for code to be written"""
    code_patterns = [
        r'write (?:a |me )?(?:python )?(?:script|code|function|program)',
        r'create (?:a |me )?(?:python )?(?:script|code|function|program)',
        r'make (?:a |me )?(?:script|code|function)',
        r'generate (?:a |me )?(?:script|code)',
        r'code (?:to|that|for)',
        r'script (?:to|that|for)',
    ]
    text_lower = text.lower()
    for pattern in code_patterns:
        if re.search(pattern, text_lower):
            filename_match = re.search(r'(?:called?|named?|save (?:as|to)?)\s+["\']?(\w+\.py)["\']?', text_lower)
            filename = filename_match.group(1) if filename_match else None
            return {'is_code_request': True, 'suggested_filename': filename}
    return {'is_code_request': False}


def extract_code_from_response(response: str) -> tuple:
    """Extract code block from LLM response"""
    code_match = re.search(r'