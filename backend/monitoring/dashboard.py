import os
import psutil
import requests
from flask import Flask, jsonify
from sqlalchemy import func
from ganuda.backend.models import Node, ThermalMemory, JrTask  # Assuming these models exist
from ganuda.backend.db import db  # Assuming this is the database instance

app = Flask(__name__)

def get_thermal_memory_stats() -> dict:
    """Fetches thermal memory statistics."""
    total_memories = ThermalMemory.query.count()
    avg_temp = db.session.query(func.avg(ThermalMemory.temperature)).scalar()
    return {
        'total_memories': total_memories,
        'avg_temperature': avg_temp
    }

def get_jr_queue_stats() -> dict:
    """Fetches JR queue statistics."""
    total_tasks = JrTask.query.count()
    pending_tasks = JrTask.query.filter_by(status='pending').count()
    return {
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks
    }

def get_node_health() -> dict:
    """Fetches node health statistics."""
    nodes = Node.query.all()
    node_health = []
    for node in nodes:
        cpu_usage = psutil.cpu_percent(interval=1)
        mem_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent
        node_health.append({
            'node_name': node.name,
            'cpu_usage': cpu_usage,
            'mem_usage': mem_usage,
            'disk_usage': disk_usage
        })
    return node_health

@app.route('/dashboard', methods=['GET'])
def dashboard() -> dict:
    """Returns a JSON response with thermal memory stats, JR queue stats, and node health."""
    thermal_memory_stats = get_thermal_memory_stats()
    jr_queue_stats = get_jr_queue_stats()
    node_health = get_node_health()
    
    return jsonify({
        'thermal_memory_stats': thermal_memory_stats,
        'jr_queue_stats': jr_queue_stats,
        'node_health': node_health
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)