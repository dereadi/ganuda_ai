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
            'host': os.environ.get('CHEROKEE_DB_HOST', '10.100.0.2'),
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
            conn.commit()
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    # ... rest of existing methods ...