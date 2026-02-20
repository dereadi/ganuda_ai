#!/usr/bin/env python3
"""
Code Generation Handler for Cherokee Chief Telegram Bot
"""

import os
import psycopg2
from datetime import datetime
from code_helper import extract_code_from_response, generate_filename_from_request

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'triad_federation',
    'user': 'claude',
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}

SCRIPTS_DIR = '/ganuda/scripts'


class CodeGenerationHandler:
    """Handles code generation requests from Telegram"""

    def __init__(self, llm_router):
        self.llm = llm_router
        os.makedirs(SCRIPTS_DIR, exist_ok=True)

    def handle_code_generation(self, text: str, code_check: dict, username: str) -> tuple:
        """Handle code generation request - generate, save, and offer to run"""
        prompt = f"""Generate Python code for this request.
Return ONLY the code in a