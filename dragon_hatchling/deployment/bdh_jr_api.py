#!/usr/bin/env python3
"""
Cherokee Dragon Hatchling Flask API Wrapper
Provides unified REST API for BDH inference across all platforms (CUDA, MPS, CPU)
"""
import sys
sys.path.insert(0, '/tmp/bdh')

from flask import Flask, request, jsonify
import torch
import bdh
import os
import time

app = Flask(__name__)

# Auto-detect best available device
if torch.cuda.is_available():
    device = torch.device('cuda')
    device_name = torch.cuda.get_device_name(0)
    print(f'🔥 Using CUDA: {device_name}')
elif torch.backends.mps.is_available() and torch.backends.mps.is_built():
    device = torch.device('mps')
    print(f'🔥 Using Apple MPS (Metal Performance Shaders)')
else:
    device = torch.device('cpu')
    print(f'⚠️ Using CPU (slower, but works everywhere)')

# Load Cherokee BDH model
CHECKPOINT_PATH = os.getenv('BDH_CHECKPOINT', '/home/dereadi/bdh_checkpoints/cherokee_bdh_v1.pt')

print(f'📊 Loading Cherokee BDH from: {CHECKPOINT_PATH}')
checkpoint = torch.load(CHECKPOINT_PATH, map_location=device, weights_only=False)
config = checkpoint['config']
model = bdh.BDH(config).to(device)
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

n_params = sum(p.numel() for p in model.parameters())
print(f'📊 Model parameters: {n_params:,} ({n_params / 1e6:.2f}M)')
print(f'✅ Cherokee Dragon Hatchling ready on {device}!')

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model': 'Cherokee BDH',
        'version': '1.0',
        'device': str(device),
        'parameters': f'{n_params / 1e6:.2f}M'
    })

@app.route('/api/bdh/ask', methods=['POST'])
def ask_bdh():
    """
    BDH inference endpoint

    Request:
    {
        "question": "Cherokee Constitutional AI",
        "max_tokens": 200,  // optional, default 200
        "top_k": 10         // optional, default 10
    }

    Response:
    {
        "answer": "...",
        "model": "Cherokee BDH 3.2M",
        "device": "cuda",
        "source": "dragon_hatchling",
        "inference_time_ms": 79.5,
        "tokens_per_sec": 629
    }
    """
    try:
        # Parse request
        data = request.json
        if not data or 'question' not in data:
            return jsonify({'error': 'Missing required field: question'}), 400

        question = data['question']
        max_tokens = data.get('max_tokens', 200)
        top_k = data.get('top_k', 10)

        # Encode prompt
        prompt = torch.tensor(
            bytearray(question, 'utf-8'),
            dtype=torch.long,
            device=device
        ).unsqueeze(0)

        # Generate response
        start_time = time.time()
        with torch.no_grad():
            output = model.generate(prompt, max_new_tokens=max_tokens, top_k=top_k)
        inference_time = time.time() - start_time

        # Decode response
        answer = bytes(output.to(torch.uint8).to('cpu').squeeze(0)).decode(errors='backslashreplace')

        return jsonify({
            'answer': answer,
            'model': f'Cherokee BDH {n_params / 1e6:.2f}M',
            'device': str(device),
            'source': 'dragon_hatchling',
            'inference_time_ms': round(inference_time * 1000, 1),
            'tokens_per_sec': round(max_tokens / inference_time, 1)
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'type': type(e).__name__
        }), 500

@app.route('/api/bdh/info', methods=['GET'])
def info():
    """Get model information"""
    return jsonify({
        'model': 'Cherokee Dragon Hatchling',
        'architecture': 'Brain-inspired with synaptic plasticity',
        'parameters': n_params,
        'parameters_human': f'{n_params / 1e6:.2f}M',
        'device': str(device),
        'checkpoint': CHECKPOINT_PATH,
        'principles': [
            'Distance=0 (local data, local training)',
            'Gadugi (neurons cooperate)',
            'Mitakuye Oyasin (scale-free network)',
            'Seven Generations (limitless context)'
        ],
        'config': {
            'n_layer': config.n_layer,
            'n_embd': config.n_embd,
            'n_head': config.n_head,
            'vocab_size': config.vocab_size
        }
    })

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Cherokee Dragon Hatchling API')
    parser.add_argument('--port', type=int, default=8010, help='Port to run on (default: 8010)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    args = parser.parse_args()

    print(f'🔥 Starting Cherokee Dragon Hatchling API on {args.host}:{args.port}')
    app.run(host=args.host, port=args.port, debug=False)
