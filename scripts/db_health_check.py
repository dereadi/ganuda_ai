import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Constants for alert thresholds
INDEX_RATIO_THRESHOLD = 5
DEAD_TUPLE_PERCENTAGE_THRESHOLD = 10
EMPTY_TABLE_SIZE_THRESHOLD = 1048576  # 1 MB
UNUSED_INDEX_SIZE_THRESHOLD = 5242880  # 5 MB

# Function to connect to the database
def connect_db() -> psycopg2.extensions.connection:
    return psycopg2.connect(
        dbname="your_db_name",
        user="your_db_user",
        password="your_db_password",
        host="your_db_host",
        port="your_db_port"
    )

# Function to run a query and fetch results
def run_query(conn: psycopg2.extensions.connection, query: str) -> List[Tuple]:
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()

# Function to compute index ratio
def compute_index_ratio(results: List[Tuple]) -> Dict[str, float]:
    index_ratios = {}
    for row in results:
        tablename, index_size, data_size = row
        if data_size > 0:
            index_ratios[tablename] = index_size / data_size
    return index_ratios

# Function to check dead tuples
def check_dead_tuples(results: List[Tuple]) -> Dict[str, float]:
    dead_tuples = {}
    for row in results:
        relname, n_dead_tup, n_live_tup = row
        if n_live_tup > 0:
            dead_tuples[relname] = (n_dead_tup / n_live_tup) * 100
    return dead_tuples

# Function to check empty tables
def check_empty_tables(results: List[Tuple]) -> Dict[str, int]:
    empty_tables = {}
    for row in results:
        relname, total_size = row
        empty_tables[relname] = total_size
    return empty_tables

# Function to check unused indexes
def check_unused_indexes(results: List[Tuple]) -> Dict[str, int]:
    unused_indexes = {}
    for row in results:
        indexrelname, index_size, idx_scan = row
        unused_indexes[indexrelname] = index_size
    return unused_indexes

# Function to log results
def log_results(results: Dict[str, any], log_file: str):
    with open(log_file, 'a') as f:
        f.write(f"{datetime.now()} - {results}\n")

# Function to send alerts
def send_alerts(alerts: Dict[str, any]):
    # Implement your alerting mechanism here (e.g., email, SMS, etc.)
    print("Alerts:", alerts)

# Main function to perform DB health checks
def db_health_check():
    conn = connect_db()
    try:
        # Run queries
        index_ratio_results = run_query(conn, """
            SELECT tablename, pg_total_relation_size - pg_relation_size as index_size, pg_relation_size as data_size 
            FROM pg_stat_user_tables
        """)
        dead_tuple_results = run_query(conn, """
            SELECT relname, n_dead_tup, n_live_tup 
            FROM pg_stat_user_tables 
            WHERE n_dead_tup > n_live_tup * 0.1
        """)
        empty_table_results = run_query(conn, """
            SELECT relname, pg_total_relation_size 
            FROM pg_stat_user_tables 
            WHERE n_live_tup = 0 AND pg_total_relation_size > 1048576
        """)
        unused_index_results = run_query(conn, """
            SELECT indexrelname, pg_relation_size(indexrelid), idx_scan 
            FROM pg_stat_user_indexes 
            WHERE idx_scan = 0 AND pg_relation_size(indexrelid) > 5242880
        """)

        # Process results
        index_ratios = compute_index_ratio(index_ratio_results)
        dead_tuples = check_dead_tuples(dead_tuple_results)
        empty_tables = check_empty_tables(empty_table_results)
        unused_indexes = check_unused_indexes(unused_index_results)

        # Log results
        log_results({
            "index_ratios": index_ratios,
            "dead_tuples": dead_tuples,
            "empty_tables": empty_tables,
            "unused_indexes": unused_indexes
        }, "db_health_log.txt")

        # Check for alerts
        alerts = {}
        for tablename, ratio in index_ratios.items():
            if ratio > INDEX_RATIO_THRESHOLD:
                alerts[f"Index Ratio Alert for {tablename}"] = ratio
        for relname, percentage in dead_tuples.items():
            if percentage > DEAD_TUPLE_PERCENTAGE_THRESHOLD:
                alerts[f"Dead Tuple Alert for {relname}"] = percentage
        for relname, size in empty_tables.items():
            if size > EMPTY_TABLE_SIZE_THRESHOLD:
                alerts[f"Empty Table Alert for {relname}"] = size
        for indexrelname, size in unused_indexes.items():
            if size > UNUSED_INDEX_SIZE_THRESHOLD:
                alerts[f"Unused Index Alert for {indexrelname}"] = size

        # Send alerts
        if alerts:
            send_alerts(alerts)

    finally:
        conn.commit()  # explicit commit before close
        conn.close()

# Function to manage the frequency of health checks
def manage_health_check_frequency(last_check_time: datetime, check_interval: timedelta) -> bool:
    return datetime.now() - last_check_time >= check_interval

# Main loop to run health checks
def main_loop():
    last_check_time = datetime.now()
    check_interval = timedelta(hours=1)
    while True:
        if manage_health_check_frequency(last_check_time, check_interval):
            db_health_check()
            last_check_time = datetime.now()

            # Graduated observation
            # If all metrics are stable, extend check to every 2 hours
            # If any metric is drifting, tighten to every 30 minutes
            # Implement this logic based on the logged results
            # For simplicity, we'll just reset the interval to 1 hour for now
            check_interval = timedelta(hours=1)

if __name__ == "__main__":
    main_loop()