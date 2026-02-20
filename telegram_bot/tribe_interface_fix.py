import psycopg2
from contextlib import contextmanager
import os

class TribeInterface:
    """Interface to the 7-Specialist Council"""

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        self.db_config = {
            'host': '192.168.132.222',
            'database': 'zammad_production',
            'user': 'claude',
            'password': os.environ.get('CHEROKEE_DB_PASS', '')
        }

    @contextmanager
    def get_db(self):
        """Get database connection as context manager"""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            yield conn
        finally:
            if conn:
                conn.close()

    # ... rest of existing methods ...