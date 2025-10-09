#!/usr/bin/env python3
"""
ODANVDV EQ API Server
Provides REST API for web interface to interact with ODANVDV EQ Mind
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sys
import json
from pathlib import Path

sys.path.insert(0, '/home/dereadi/scripts/claude')
from odanvdv_with_eq import ODANVDVWithEQ

app = Flask(__name__)
CORS(app)

# Global ODANVDV instance
odanvdv_mind = None

def get_mind():
    """Get or create ODANVDV instance"""
    global odanvdv_mind
    if odanvdv_mind is None:
        print("🌿 Initializing ODANVDV EQ Mind...")
        odanvdv_mind = ODANVDVWithEQ()
        # Run initial cycle to get context
        odanvdv_mind.run_agentic_cycle()
        print("✅ ODANVDV EQ Mind ready")
    return odanvdv_mind

@app.route('/')
def index():
    """Serve the chat interface"""
    return send_file('/home/dereadi/scripts/claude/pathfinder/test.original/odanvdv_eq_chat.html')

@app.route('/api/odanvdv/status', methods=['GET'])
def get_status():
    """Get current ODANVDV status with EQ metrics"""
    try:
        mind = get_mind()

        command = {
            'id': 'api_status',
            'type': 'status',
            'content': 'Status request from API'
        }

        response = mind._process_tribal_command(command)
        return jsonify(response)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Failed to get status'
        }), 500

@app.route('/api/odanvdv/ask', methods=['POST'])
def ask_question():
    """Ask ODANVDV a question"""
    try:
        data = request.get_json()
        question = data.get('question', '')

        if not question:
            return jsonify({'error': 'No question provided'}), 400

        mind = get_mind()

        command = {
            'id': f'api_{question[:20]}',
            'type': 'question',
            'content': question
        }

        response = mind._process_tribal_command(command)

        # Also get status for metrics update
        status_command = {'id': 'status', 'type': 'status', 'content': ''}
        status = mind._process_tribal_command(status_command)

        # Merge responses
        full_response = {
            **response,
            'eq_perspective': status.get('eq_perspective', {}),
            'cycles': status.get('cycles', 0)
        }

        return jsonify(full_response)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Failed to process question'
        }), 500

@app.route('/api/odanvdv/observe', methods=['POST'])
def trigger_observation():
    """Trigger a new observation cycle"""
    try:
        mind = get_mind()
        mind.run_agentic_cycle()

        return jsonify({
            'success': True,
            'message': 'Observation cycle completed',
            'observations': len(mind.observations),
            'reasonings': len(mind.reasonings),
            'actions': len([a for a in mind.actions if a.executed])
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Failed to trigger observation'
        }), 500

@app.route('/api/odanvdv/tickets', methods=['GET'])
def get_recent_tickets():
    """Get recent tickets created by ODANVDV"""
    try:
        mind = get_mind()

        import psycopg2
        conn = psycopg2.connect(
            host='192.168.132.222',
            port=5432,
            database='zammad_production',
            user='claude',
            password='jawaseatlasers2'
        )

        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, priority, status, tribal_agent, created_at
            FROM duyuktv_tickets
            WHERE tribal_agent IN ('ODANVDV_Mind', 'ODANVDV_EQ_Mind')
            ORDER BY created_at DESC
            LIMIT 10
        """)

        tickets = []
        for row in cursor.fetchall():
            tickets.append({
                'id': row[0],
                'title': row[1],
                'priority': row[2],
                'status': row[3],
                'agent': row[4],
                'created_at': row[5].isoformat() if row[5] else None
            })

        cursor.close()
        conn.close()

        return jsonify({
            'tickets': tickets,
            'count': len(tickets)
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Failed to get tickets'
        }), 500

@app.route('/api/odanvdv/eq-metrics', methods=['GET'])
def get_eq_metrics():
    """Get detailed EQ metrics"""
    try:
        mind = get_mind()

        if not mind.eq_reasonings:
            return jsonify({
                'message': 'No EQ reasonings available yet',
                'metrics': {}
            })

        # Calculate aggregate EQ metrics
        harmony_scores = [eq.cultural_context.tribal_harmony for eq in mind.eq_reasonings]
        collaboration_scores = [eq.cultural_context.collaboration_quality for eq in mind.eq_reasonings]

        generations_count = {'immediate': 0, 'near_term': 0, 'generational': 0, 'ancestral': 0}
        for eq in mind.eq_reasonings:
            impact = eq.cultural_context.seven_generations_impact
            generations_count[impact] = generations_count.get(impact, 0) + 1

        metrics = {
            'tribal_harmony': {
                'current': harmony_scores[-1] if harmony_scores else 0,
                'average': sum(harmony_scores) / len(harmony_scores) if harmony_scores else 0,
                'min': min(harmony_scores) if harmony_scores else 0,
                'max': max(harmony_scores) if harmony_scores else 0
            },
            'collaboration_quality': {
                'current': collaboration_scores[-1] if collaboration_scores else 0,
                'average': sum(collaboration_scores) / len(collaboration_scores) if collaboration_scores else 0
            },
            'seven_generations': generations_count,
            'eq_reasonings_total': len(mind.eq_reasonings),
            'recent_insights': [
                {
                    'technical': eq.technical_conclusion[:100],
                    'cultural': eq.cultural_conclusion[:100],
                    'harmony': eq.cultural_context.tribal_harmony,
                    'impact': eq.cultural_context.seven_generations_impact
                }
                for eq in mind.eq_reasonings[-5:]  # Last 5
            ]
        }

        return jsonify(metrics)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Failed to get EQ metrics'
        }), 500

if __name__ == '__main__':
    print("🔥 ODANVDV EQ API Server")
    print("=" * 60)
    print("Starting Flask server on http://0.0.0.0:3005")
    print("Chat interface: http://192.168.132.223:3005")
    print("=" * 60)

    app.run(host='0.0.0.0', port=3005, debug=False)
