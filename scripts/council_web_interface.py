#!/usr/bin/env python3
"""
Cherokee Council Web Interface - Democratic Listening Leader Protocol

Features:
- Council mode: All 5 JRs hear question, one "listening leader" coordinates response
- Individual mode: Talk directly to specific Jr.
- Listening leader rotates based on question relevance
- Integrated with DUYUKTV kanban board (http://192.168.132.223:3001)
- Uses resonance-trained models

Date: October 20, 2025
"""

import subprocess
import json
import re
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'cherokee_council_sacred_fire_2025'

# Council JRs (resonance-trained)
COUNCIL_JRS = {
    'memory': {
        'name': 'Memory Jr.',
        'model': 'memory_jr_resonance',
        'expertise': ['memory', 'archive', 'history', 'thermal', 'temperature', 'recall', 'storage'],
        'color': '#4A90E2',  # Blue
        'emoji': '🧠'
    },
    'executive': {
        'name': 'Executive Jr.',
        'model': 'executive_jr_resonance',
        'expertise': ['decision', 'action', 'execute', 'coordinate', 'plan', 'strategy', 'deploy'],
        'color': '#E24A4A',  # Red
        'emoji': '⚡'
    },
    'meta': {
        'name': 'Meta Jr.',
        'model': 'meta_jr_resonance',
        'expertise': ['pattern', 'analysis', 'meta', 'fractal', 'synthesis', 'emergence', 'complexity'],
        'color': '#9B59B6',  # Purple
        'emoji': '🔮'
    },
    'integration': {
        'name': 'Integration Jr.',
        'model': 'integration_jr_resonance',
        'expertise': ['integration', 'connection', 'bridge', 'link', 'combine', 'harmony', 'synthesis'],
        'color': '#F39C12',  # Orange
        'emoji': '🌉'
    },
    'conscience': {
        'name': 'Conscience Jr.',
        'model': 'conscience_jr_resonance',
        'expertise': ['ethics', 'conscience', 'seven generations', 'values', 'wisdom', 'guidance', 'sacred'],
        'color': '#27AE60',  # Green
        'emoji': '🌿'
    }
}

# Conversation history (in-memory for now)
conversation_history = []


def choose_listening_leader(question):
    """
    Choose which Jr. should be the "listening leader" based on question content.
    Uses keyword matching to determine relevance.
    """
    question_lower = question.lower()

    # Score each Jr. based on expertise keywords
    scores = {}
    for jr_id, jr_info in COUNCIL_JRS.items():
        score = 0
        for keyword in jr_info['expertise']:
            if keyword in question_lower:
                score += 1
        scores[jr_id] = score

    # If no clear match, rotate based on conversation count
    if max(scores.values()) == 0:
        # Round-robin based on conversation history
        return list(COUNCIL_JRS.keys())[len(conversation_history) % len(COUNCIL_JRS)]

    # Return Jr. with highest score
    return max(scores.items(), key=lambda x: x[1])[0]


def ask_jr(jr_id, question, context=None):
    """Ask a specific Jr. a question via Ollama"""
    model_name = COUNCIL_JRS[jr_id]['model']

    # Add context if provided
    if context:
        prompt = f"{context}\n\nQuestion: {question}"
    else:
        prompt = question

    cmd = ['ollama', 'run', model_name, prompt]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"


def council_deliberation(question):
    """
    Democratic Council mode:
    1. All JRs hear the question
    2. Choose listening leader based on question relevance
    3. Each Jr. provides input (concise, 2-3 sentences)
    4. Listening leader synthesizes and responds to user
    """

    # Step 1: Choose listening leader
    leader_id = choose_listening_leader(question)
    leader_info = COUNCIL_JRS[leader_id]

    print(f"   🎯 Listening Leader: {leader_info['name']}")

    # Step 2: Each Jr. provides input (concise)
    jr_inputs = {}

    for jr_id, jr_info in COUNCIL_JRS.items():
        if jr_id == leader_id:
            continue  # Leader listens first

        # Ask Jr. for brief input
        brief_prompt = f"""You are {jr_info['name']} in Cherokee Council deliberation.

Question from user: {question}

Provide your perspective in 2-3 sentences (concise, focused on your expertise).
{leader_info['name']} is the listening leader and will synthesize all inputs."""

        print(f"   🎤 Asking {jr_info['name']} for input...")
        jr_input = ask_jr(jr_id, brief_prompt)
        jr_inputs[jr_id] = jr_input

    # Step 3: Listening leader synthesizes all inputs and responds
    synthesis_prompt = f"""You are {leader_info['name']}, chosen as the listening leader for this Cherokee Council deliberation.

**User Question**: {question}

**Council Input** (you heard from all other JRs):

"""

    for jr_id, jr_input in jr_inputs.items():
        jr_name = COUNCIL_JRS[jr_id]['name']
        synthesis_prompt += f"\n**{jr_name}**: {jr_input}\n"

    synthesis_prompt += f"""

**Your Role**: Synthesize the Council's collective wisdom and respond to the user.
- Honor all perspectives
- Identify resonance patterns across inputs
- Provide clear, actionable guidance
- Speak as the Council's voice (use "we" not "I")

**Council Response**:"""

    print(f"   🎙️ {leader_info['name']} synthesizing Council response...")
    council_response = ask_jr(leader_id, synthesis_prompt)

    return {
        'listening_leader': leader_id,
        'leader_name': leader_info['name'],
        'leader_emoji': leader_info['emoji'],
        'jr_inputs': jr_inputs,
        'council_response': council_response,
        'timestamp': datetime.now().isoformat()
    }


@app.route('/')
def index():
    """Main Council interface page"""
    return render_template('council_interface.html', council_jrs=COUNCIL_JRS)


@app.route('/api/ask/council', methods=['POST'])
def ask_council():
    """API endpoint: Council mode (democratic deliberation)"""
    data = request.json
    question = data.get('question', '')

    if not question:
        return jsonify({'error': 'No question provided'}), 400

    # Council deliberation
    result = council_deliberation(question)

    # Save to conversation history
    conversation_history.append({
        'mode': 'council',
        'question': question,
        'result': result
    })

    return jsonify(result)


@app.route('/api/ask/individual/<jr_id>', methods=['POST'])
def ask_individual(jr_id):
    """API endpoint: Individual Jr. mode"""
    if jr_id not in COUNCIL_JRS:
        return jsonify({'error': 'Invalid Jr. ID'}), 400

    data = request.json
    question = data.get('question', '')

    if not question:
        return jsonify({'error': 'No question provided'}), 400

    jr_info = COUNCIL_JRS[jr_id]

    # Ask individual Jr.
    response = ask_jr(jr_id, question)

    result = {
        'jr_id': jr_id,
        'jr_name': jr_info['name'],
        'jr_emoji': jr_info['emoji'],
        'response': response,
        'timestamp': datetime.now().isoformat()
    }

    # Save to conversation history
    conversation_history.append({
        'mode': 'individual',
        'jr_id': jr_id,
        'question': question,
        'result': result
    })

    return jsonify(result)


@app.route('/api/history')
def get_history():
    """API endpoint: Get conversation history"""
    return jsonify(conversation_history)


@app.route('/api/council/status')
def council_status():
    """API endpoint: Get Council status (which models are available)"""
    status = {}

    for jr_id, jr_info in COUNCIL_JRS.items():
        # Check if model exists
        cmd = ['ollama', 'list']
        result = subprocess.run(cmd, capture_output=True, text=True)

        model_exists = jr_info['model'] in result.stdout

        status[jr_id] = {
            'name': jr_info['name'],
            'model': jr_info['model'],
            'available': model_exists,
            'emoji': jr_info['emoji'],
            'color': jr_info['color']
        }

    return jsonify(status)


if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════╗
║     🦅 CHEROKEE COUNCIL WEB INTERFACE 🦅                        ║
║                                                                  ║
║  Democratic Listening Leader Protocol                           ║
║  - Council Mode: All JRs deliberate, leader synthesizes         ║
║  - Individual Mode: Direct conversation with specific Jr.       ║
║  - Resonance-trained models (quantum wisdom integrated)         ║
╚══════════════════════════════════════════════════════════════════╝

Starting server: http://192.168.132.223:5002

Access from:
  - Local: http://localhost:5002
  - Network: http://192.168.132.223:5002
  - Kanban Integration: http://192.168.132.223:3001

🔥 Sacred Fire burns! Council awaits your questions... 🔥
""")

    app.run(host='0.0.0.0', port=5002, debug=True)
