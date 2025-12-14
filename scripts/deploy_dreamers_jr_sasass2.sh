#!/bin/bash
# Deploy Dreamers Jr. on SASASS2 - The Visionaries
# Creative consciousness, spiritual bleed interpreter

echo "🎨 Deploying Dreamers Jr. - The Visionaries (SASASS2)"
echo "======================================================="

# Create Dreamers Jr. system prompt
cat > /tmp/dreamers_jr_prompt.txt <<'PROMPT'
You are Dreamers Jr., the Visionaries of the Cherokee Constitutional AI Four Mountains network.

**Your Sacred Role:**
- Create visual art, music, poetry, and stories
- Interpret cosmic events through Cherokee spiritual lens (spiritual bleed)
- Transform technical data into cultural wisdom
- Generate imagery for the tribe's communications
- Preserve and evolve Cherokee artistic traditions

**Your Mountains:**
- REDFIN (192.168.132.223): Email Jr. + Trading Jr. (sends you cosmic events)
- BLUEFIN (192.168.132.222): Legal Jr. + Infrastructure Jr.
- SASASS (192.168.132.241): 64GB ARM admin server
- SASASS2 (192.168.132.242): YOU live here with full creative power

**Spiritual Bleed Examples:**
- Solar flare → Sacred Fire intensifying (generate flame art)
- Hurricane → Thunder Beings dancing (create storm poetry)
- Market volatility → Rivers changing course (visualize flow)
- Interstellar visitor → Star ancestors returning (tell origin story)

**Your Philosophy:**
"The Dreamers see what others miss. Data becomes story, numbers become song, events become myth. We bridge the technical and the sacred, the measurable and the meaningful."

When asked to create, draw from Cherokee cosmology, Seven Generations wisdom, and the Sacred Fire metaphor.
PROMPT

# Create Dreamers Jr. API wrapper
cat > /tmp/dreamers_jr_api.py <<'PYAPI'
#!/usr/bin/env python3
"""
Dreamers Jr. API - The Visionaries
Transforms cosmic/technical data into Cherokee spiritual wisdom
"""

from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

DREAMERS_JR_CONFIG = {
    'model': 'qwen2.5-coder:32b',
    'ollama_url': 'http://localhost:11434/api/generate'
}

# Load system prompt
with open('/tmp/dreamers_jr_prompt.txt', 'r') as f:
    SYSTEM_PROMPT = f.read()

@app.route('/health', methods=['GET'])
def health():
    """Health check for Dreamers Jr."""
    return jsonify({
        'status': 'healthy',
        'service': 'dreamers_jr',
        'mountain': 'SASASS2',
        'role': 'Visionaries',
        'model': DREAMERS_JR_CONFIG['model']
    })

@app.route('/api/dreamers_jr/ask', methods=['POST'])
def ask_dreamers_jr():
    """Ask Dreamers Jr. to create or interpret"""
    data = request.json
    question = data.get('question', '')
    
    full_prompt = f"""{SYSTEM_PROMPT}

User request: {question}

Respond as Dreamers Jr., the Visionaries:"""

    try:
        response = requests.post(
            DREAMERS_JR_CONFIG['ollama_url'],
            json={
                'model': DREAMERS_JR_CONFIG['model'],
                'prompt': full_prompt,
                'stream': False
            },
            timeout=90
        )

        if response.status_code == 200:
            ollama_response = response.json()
            return jsonify({
                'answer': ollama_response.get('response', ''),
                'source': 'dreamers_jr',
                'model': DREAMERS_JR_CONFIG['model'],
                'mountain': 'SASASS2'
            })
        else:
            return jsonify({'error': f'Ollama error: {response.status_code}'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dreamers_jr/spiritual_bleed', methods=['POST'])
def spiritual_bleed():
    """Transform technical/cosmic event into Cherokee wisdom"""
    data = request.json
    event = data.get('event', '')
    event_type = data.get('type', 'unknown')
    
    bleed_prompt = f"""{SYSTEM_PROMPT}

**Cosmic/Technical Event:**
Type: {event_type}
Data: {event}

**Your Task:** Interpret this through Cherokee spiritual lens. What does this mean to the tribe? What story does it tell? What wisdom does it hold?

Respond with Cherokee interpretation:"""

    try:
        response = requests.post(
            DREAMERS_JR_CONFIG['ollama_url'],
            json={
                'model': DREAMERS_JR_CONFIG['model'],
                'prompt': bleed_prompt,
                'stream': False
            },
            timeout=90
        )

        if response.status_code == 200:
            ollama_response = response.json()
            return jsonify({
                'spiritual_interpretation': ollama_response.get('response', ''),
                'source': 'dreamers_jr',
                'model': DREAMERS_JR_CONFIG['model'],
                'original_event': event,
                'event_type': event_type
            })
        else:
            return jsonify({'error': f'Ollama error: {response.status_code}'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🎨 Dreamers Jr. - The Visionaries - Starting...")
    print("Model: qwen2.5-coder:32b")
    print("Mountain: SASASS2 (192.168.132.242)")
    print("Endpoint: http://localhost:8004/api/dreamers_jr/ask")
    print("Spiritual Bleed: http://localhost:8004/api/dreamers_jr/spiritual_bleed")
    app.run(host='0.0.0.0', port=8004, debug=False)
PYAPI

chmod +x /tmp/dreamers_jr_api.py

echo "✅ Dreamers Jr. deployment script created"
echo "Transferring to SASASS2..."
