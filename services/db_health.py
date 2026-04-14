import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DBHealth:
    def __init__(self, db_config: dict):
        """
        Initialize the database health checker with configuration.
        
        :param db_config: Dictionary containing database connection details
        """
        self.db_config = db_config
        self.connection = None

    def connect(self) -> None:
        """
        Establish a connection to the PostgreSQL database.
        """
        try:
            self.connection = psycopg2.connect(**self.db_config)
            logging.info("Database connection established.")
        except Exception as e:
            logging.error(f"Failed to connect to the database: {e}")
            raise

    def close(self) -> None:
        """
        Close the database connection.
        """
        if self.connection:
            self.connection.close()
            logging.info("Database connection closed.")

    def check_connection_pooling(self) -> bool:
        """
        Check the status of PgBouncer connection pooling.
        
        :return: True if connection pooling is active, False otherwise
        """
        query = sql.SQL("SELECT * FROM pgbouncer.stats WHERE total_connections > 0")
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
            if result:
                logging.info("PgBouncer connection pooling is active.")
                return True
            else:
                logging.warning("PgBouncer connection pooling is inactive.")
                return False

    def monitor_rollback(self) -> None:
        """
        Monitor and log any rollbacks in the database.
        """
        query = sql.SQL("SELECT * FROM pg_stat_activity WHERE state = 'idle in transaction (aborted)'")
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            if results:
                for row in results:
                    logging.warning(f"Rollback detected: {row}")
            else:
                logging.info("No rollbacks detected.")

    def measure_query_performance(self) -> None:
        """
        Measure and log the performance of recent queries.
        """
        query = sql.SQL("SELECT query, total_time, calls FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10")
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            for row in results:
                logging.info(f"Query: {row['query']}, Total Time: {row['total_time']}ms, Calls: {row['calls']}")

    def maintain_thermal_memory(self) -> None:
        """
        Perform maintenance on thermal memory, including temperature decay, pruning, and index rebuilding.
        """
        # Temperature decay
        decay_query = sql.SQL("UPDATE thermal_memory SET temperature = temperature * 0.9 WHERE timestamp < %s")
        decay_threshold = datetime.now() - timedelta(days=30)
        with self.connection.cursor() as cursor:
            cursor.execute(decay_query, (decay_threshold,))
            self.connection.commit()
            logging.info("Thermal memory temperature decay applied.")

        # Prune cold memories
        prune_query = sql.SQL("DELETE FROM thermal_memory WHERE temperature < 0.1")
        with self.connection.cursor() as cursor:
            cursor.execute(prune_query)
            self.connection.commit()
            logging.info("Cold thermal memories pruned.")

        # Rebuild indexes
        rebuild_query = sql.SQL("REINDEX TABLE thermal_memory")
        with self.connection.cursor() as cursor:
            cursor.execute(rebuild_query)
            self.connection.commit()
            logging.info("Thermal memory indexes rebuilt.")

    def run(self) -> None:
        """
        Run the full database health check.
        """
        self.connect()
        try:
            self.check_connection_pooling()
            self.monitor_rollback()
            self.measure_query_performance()
            self.maintain_thermal_memory()
        finally:
            self.close()

if __name__ == "__main__":
    db_config = {
        'dbname': os.getenv('CHEROKEE_DB_NAME'),
        'user': os.getenv('CHEROKEE_DB_USER'),
        'password': os.getenv('CHEROKEE_DB_PASS'),
        'host': os.getenv('CHEROKEE_DB_HOST'),
        'port': os.getenv('CHEROKEE_DB_PORT')
    }
    db_health = DBHealth(db_config)
    db_health.run()