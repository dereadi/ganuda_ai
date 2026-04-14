import psutil
import time
from typing import List, Dict
from flask import Flask, jsonify

app = Flask(__name__)

def get_thermal_memory_stats() -> Dict[str, float]:
    """
    Collects and returns the thermal memory statistics.
    """
    # Simulate thermal memory data
    total_memories = 96077
    avg_temp = 36.4
    max_temp = 59.0
    min_temp = 25.0
    
    return {
        "total_memories": total_memories,
        "avg_temp": avg_temp,
        "max_temp": max_temp,
        "min_temp": min_temp
    }

@app.route('/api/thermal_memory_stats', methods=['GET'])
def thermal_memory_stats() -> str:
    """
    Endpoint to get the current thermal memory statistics.
    """
    stats = get_thermal_memory_stats()
    return jsonify(stats)

def monitor_thermal_memory(interval: int = 60) -> None:
    """
    Periodically logs the thermal memory statistics to the console.
    
    :param interval: Interval in seconds between each log.
    """
    while True:
        stats = get_thermal_memory_stats()
        print(f"Thermal Memory Stats: {stats}")
        time.sleep(interval)

if __name__ == '__main__':
    # Start the monitoring thread
    import threading
    monitoring_thread = threading.Thread(target=monitor_thermal_memory, daemon=True)
    monitoring_thread.start()
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=5000)