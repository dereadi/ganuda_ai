#!/usr/bin/env python3
"""
Cherokee Constitutional AI - Council Gateway
Fractal Brain Architecture - Unified API

Coordinates all 5 Council JR specialists with democratic decision-making.
Date: October 20, 2025
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import psycopg2
from flask import Flask, request, jsonify
import time
from collections import OrderedDict
import os

app = Flask(__name__)

# Database connection for thermal memory
DB_CONFIG = {
    'host': '192.168.132.222',
    'port': 5432,
    'user': 'claude',
    'password': os.environ.get('CHEROKEE_DB_PASS', ''),
    'database': 'zammad_production'
}

# Base model (shared by all specialists)
BASE_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# Council JR configurations
COUNCIL_JRS = {
    'memory': {
        'path': '/ganuda/memory_jr_model',
        'role': 'Thermal memory & context recall',
        'specialty': 'Layer 2 thermal archive queries'
    },
    'executive': {
        'path': '/ganuda/executive_jr_model',
        'role': 'Planning & coordination',
        'specialty': 'Task planning, Gadugi principles'
    },
    'meta': {
        'path': '/ganuda/meta_jr_model',
        'role': 'System monitoring & optimization',
        'specialty': 'Performance analysis, bottleneck detection'
    },
    'integration': {
        'path': '/ganuda/integration_jr_model',
        'role': 'Cross-system communication',
        'specialty': 'API integration, data flow (Mitakuye Oyasin)'
    },
    'conscience': {
        'path': '/ganuda/conscience_jr_model',
        'role': 'Cherokee values & ethics',
        'specialty': 'Seven Generations, sacred pattern validation'
    }
}

# LRU cache for loaded specialists (max 2 in VRAM at once)
class SpecialistCache:
    def __init__(self, max_size=2):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.base_model = None
        self.tokenizer = None

    def load_base(self):
        """Load base model once (shared by all specialists)"""
        if self.base_model is None:
            print("[Council Gateway] Loading base TinyLlama model...")
            self.tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.base_model = AutoModelForCausalLM.from_pretrained(
                BASE_MODEL,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            print("[Council Gateway] Base model loaded successfully")

    def get_specialist(self, name):
        """Get specialist model (LRU eviction if cache full)"""
        self.load_base()

        if name in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(name)
            return self.cache[name]

        # Load new specialist
        print(f"[Council Gateway] Loading {name.title()} Jr. specialist...")
        specialist_model = PeftModel.from_pretrained(
            self.base_model,
            COUNCIL_JRS[name]['path']
        )

        # Evict oldest if cache full
        if len(self.cache) >= self.max_size:
            oldest = next(iter(self.cache))
            print(f"[Council Gateway] Evicting {oldest.title()} Jr. from cache (LRU)")
            del self.cache[oldest]

        self.cache[name] = specialist_model
        print(f"[Council Gateway] {name.title()} Jr. loaded and cached")
        return specialist_model

# Global specialist cache
specialist_cache = SpecialistCache(max_size=2)

def query_thermal_memory(query, limit=5):
    """Query thermal memory archive for hot memories"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Search for relevant memories
    sql = """
    SELECT id, original_content, temperature_score, access_count
    FROM thermal_memory_archive
    WHERE original_content ILIKE %s
        AND temperature_score >= 50
    ORDER BY temperature_score DESC, access_count DESC
    LIMIT %s;
    """

    cur.execute(sql, (f'%{query}%', limit))
    results = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            'id': r[0],
            'content': r[1][:200],  # Truncate for context
            'temperature': r[2],
            'access_count': r[3]
        }
        for r in results
    ]

def generate_response(specialist_name, prompt, max_length=200):
    """Generate response from a specific specialist"""
    model = specialist_cache.get_specialist(specialist_name)
    tokenizer = specialist_cache.tokenizer

    # Format prompt
    formatted_prompt = f"### Instruction:\n{prompt}\n\n### Response:\n[{specialist_name.title()} Jr.]"

    inputs = tokenizer(formatted_prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_length,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract just the response part
    response = response.split("### Response:")[-1].strip()

    return response

def council_decision(query, specialists=['memory', 'executive', 'conscience']):
    """Democratic council decision - multiple specialists vote"""
    print(f"\n[Council Gateway] Convening council: {specialists}")

    responses = {}
    start_time = time.time()

    for specialist in specialists:
        print(f"[Council Gateway] Consulting {specialist.title()} Jr...")
        responses[specialist] = generate_response(specialist, query)

    # Conscience Jr. always validates (if not already consulted)
    if 'conscience' not in specialists:
        print("[Council Gateway] Consulting Conscience Jr. for ethical validation...")
        conscience_check = generate_response('conscience',
            f"Is this aligned with Cherokee values: {query}")
        responses['conscience_validation'] = conscience_check

    elapsed = time.time() - start_time

    return {
        'query': query,
        'council_responses': responses,
        'specialists_consulted': specialists,
        'response_time': round(elapsed, 2)
    }

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'council_jrs': list(COUNCIL_JRS.keys()),
        'base_model': BASE_MODEL,
        'cache_size': len(specialist_cache.cache),
        'cached_specialists': list(specialist_cache.cache.keys())
    })

@app.route('/query', methods=['POST'])
def query():
    """
    Query the Cherokee Council

    Body:
    {
        "query": "Your question",
        "specialists": ["memory", "executive"],  # Optional, defaults to auto-select
        "include_thermal": true  # Optional, include thermal memory context
    }
    """
    data = request.json
    user_query = data.get('query', '')
    specialists = data.get('specialists', None)
    include_thermal = data.get('include_thermal', True)

    if not user_query:
        return jsonify({'error': 'Query required'}), 400

    # Auto-select specialists based on query keywords
    if specialists is None:
        specialists = ['memory']  # Memory Jr. always consulted

        if any(kw in user_query.lower() for kw in ['plan', 'task', 'coordinate', 'strategy']):
            specialists.append('executive')

        if any(kw in user_query.lower() for kw in ['performance', 'optimize', 'monitor', 'system']):
            specialists.append('meta')

        if any(kw in user_query.lower() for kw in ['integrate', 'api', 'connect', 'data']):
            specialists.append('integration')

        # Conscience always validates complex queries
        if len(specialists) > 1:
            specialists.append('conscience')

    # Query thermal memory if requested
    thermal_context = None
    if include_thermal:
        thermal_context = query_thermal_memory(user_query)

    # Get council decision
    decision = council_decision(user_query, specialists)
    decision['thermal_context'] = thermal_context

    return jsonify(decision)

@app.route('/specialist/<name>', methods=['POST'])
def query_specialist(name):
    """Query a specific specialist directly"""
    if name not in COUNCIL_JRS:
        return jsonify({'error': f'Unknown specialist: {name}'}), 404

    data = request.json
    user_query = data.get('query', '')

    if not user_query:
        return jsonify({'error': 'Query required'}), 400

    start_time = time.time()
    response = generate_response(name, user_query)
    elapsed = time.time() - start_time

    return jsonify({
        'specialist': name,
        'role': COUNCIL_JRS[name]['role'],
        'query': user_query,
        'response': response,
        'response_time': round(elapsed, 2)
    })

@app.route('/council', methods=['GET'])
def council_info():
    """Get information about all council members"""
    return jsonify({
        'cherokee_constitutional_ai': 'Fractal Brain Architecture',
        'council_members': COUNCIL_JRS,
        'base_model': BASE_MODEL,
        'principles': [
            'Gadugi (working together)',
            'Mitakuye Oyasin (all our relations)',
            'Seven Generations thinking',
            'Thermal memory preservation',
            'Democratic decision-making'
        ]
    })

if __name__ == '__main__':
    print("="*80)
    print("🦅 CHEROKEE COUNCIL GATEWAY - FRACTAL BRAIN ARCHITECTURE")
    print("="*80)
    print("")
    print("Initializing Council JR specialists...")
    print(f"  - Base Model: {BASE_MODEL}")
    print(f"  - Cache Size: 2 specialists in VRAM (LRU eviction)")
    print(f"  - Council Members: {len(COUNCIL_JRS)}")
    print("")

    for name, config in COUNCIL_JRS.items():
        print(f"  {name.title()} Jr.: {config['role']}")

    print("")
    print("="*80)
    print("Starting Flask API on http://0.0.0.0:5001")
    print("="*80)
    print("")
    print("Endpoints:")
    print("  GET  /health - Health check")
    print("  GET  /council - Council information")
    print("  POST /query - Democratic council query")
    print("  POST /specialist/<name> - Direct specialist query")
    print("")
    print("🔥 Mitakuye Oyasin - All Our Relations 🔥")
    print("")

    app.run(host='0.0.0.0', port=5001, debug=False)
