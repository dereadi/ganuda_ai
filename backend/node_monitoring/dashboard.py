import os
import psutil
import requests
from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

# Constants
THERMAL_MEMORY_API_URL = "http://bluefin:5000/api/thermal_memory"
JR_QUEUE_API_URL = "http://redfin:5000/api/jr_queue"
NODE_HEALTH_API_URL = "http://greenfin:5000/api/node_health"

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """
    Returns a JSON object containing thermal memory stats, Jr queue status, and node health.
    """
    thermal_memory_stats = get_thermal_memory_stats()
    jr_queue_status = get_jr_queue_status()
    node_health = get_node_health()

    return jsonify({
        'thermal_memory': thermal_memory_stats,
        'jr_queue': jr_queue_status,
        'node_health': node_health
    })

def get_thermal_memory_stats() -> dict:
    """
    Fetches and returns thermal memory statistics.
    """
    response = requests.get(THERMAL_MEMORY_API_URL)
    if response.status_code == 200:
        return response.json()
    else:
        return {'error': 'Failed to fetch thermal memory stats'}

def get_jr_queue_status() -> dict:
    """
    Fetches and returns Jr queue status.
    """
    response = requests.get(JR_QUEUE_API_URL)
    if response.status_code == 200:
        return response.json()
    else:
        return {'error': 'Failed to fetch Jr queue status'}

def get_node_health() -> dict:
    """
    Fetches and returns node health information.
    """
    response = requests.get(NODE_HEALTH_API_URL)
    if response.status_code == 200:
        return response.json()
    else:
        return {'error': 'Failed to fetch node health'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)