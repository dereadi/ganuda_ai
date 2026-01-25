# JR Instruction: Setup MLX on sasass Mac Studio
## Task ID: MLX-SETUP-001
## Priority: P2
## Target: sasass (192.168.132.241)

---

## Objective

Install MLX and MLX-LM on sasass Mac Studio (64GB) to enable local inference for JR instruction parsing, reducing load on redfin vLLM.

---

## Implementation

### Step 1: Install MLX via pip

```bash
ssh sasass "pip3 install --user mlx mlx-lm"
```

### Step 2: Download a small instruction-following model

```bash
ssh sasass "python3 -m mlx_lm.convert --hf-path Qwen/Qwen2.5-3B-Instruct -q"
```

### Step 3: Test MLX inference

```bash
ssh sasass "python3 -m mlx_lm.generate --model Qwen/Qwen2.5-3B-Instruct --prompt 'Extract the file path from: Create \`/ganuda/lib/test.py\`:' --max-tokens 50"
```

### Step 4: Create MLX inference service

Create `/Users/Shared/ganuda/services/mlx_inference.py`:

```python
#!/usr/bin/env python3
"""
MLX Inference Service for JR Instruction Parsing
Cherokee AI Federation - sasass Mac Studio
"""

from flask import Flask, request, jsonify
from mlx_lm import load, generate

app = Flask(__name__)

# Load model once at startup
MODEL_PATH = "mlx-community/Qwen2.5-3B-Instruct-4bit"
model, tokenizer = None, None

def get_model():
    global model, tokenizer
    if model is None:
        model, tokenizer = load(MODEL_PATH)
    return model, tokenizer

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "model": MODEL_PATH})

@app.route('/parse', methods=['POST'])
def parse_instruction():
    """Parse JR instruction and extract executable steps."""
    data = request.json
    instruction = data.get('instruction', '')

    prompt = f"""Extract file creation steps from this instruction.
For each file, output: FILE: /path/to/file

Instruction:
{instruction[:2000]}

Files to create:"""

    model, tokenizer = get_model()
    response = generate(model, tokenizer, prompt=prompt, max_tokens=200)

    # Parse response for file paths
    import re
    files = re.findall(r'FILE:\s*(/[^\s]+)', response)

    return jsonify({
        "files": files,
        "raw_response": response
    })

if __name__ == '__main__':
    print("Loading model...")
    get_model()
    print("Starting MLX inference service on port 8090...")
    app.run(host='0.0.0.0', port=8090)
```

---

## Verification

```bash
# Test health endpoint
curl http://192.168.132.241:8090/health

# Test parsing
curl -X POST http://192.168.132.241:8090/parse \
  -H "Content-Type: application/json" \
  -d '{"instruction": "Create `/ganuda/lib/test.py`:\n```python\nprint(hello)\n```"}'
```

---

## Integration with JR Executor

Add to task_executor.py option to use sasass for instruction parsing when redfin is overloaded.

---

*Cherokee AI Federation - For Seven Generations*
