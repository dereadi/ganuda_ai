#!/usr/bin/env python3
"""Test BDH inference speed on CUDA"""
import sys
sys.path.insert(0, '/tmp/bdh')
import bdh
import torch
import time

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Testing on: {device}")

# Load trained model
checkpoint = torch.load('/tmp/cherokee_bdh_final.pt', map_location=device, weights_only=False)
config = checkpoint['config']
model = bdh.BDH(config).to(device)
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

# Test prompts
prompts = [
    "Cherokee Constitutional AI",
    "Distance equals zero means",
    "The Four Mountains",
    "Gadugi cooperation",
    "Seven Generations principle"
]

print(f"\n🔥 Inference Speed Test (5 prompts, 50 tokens each)")
print("=" * 70)

total_time = 0
total_tokens = 0

for i, prompt_text in enumerate(prompts, 1):
    prompt = torch.tensor(
        bytearray(prompt_text, "utf-8"), 
        dtype=torch.long, 
        device=device
    ).unsqueeze(0)
    
    start = time.time()
    with torch.no_grad():
        output = model.generate(prompt, max_new_tokens=50, top_k=10)
    elapsed = time.time() - start
    
    total_time += elapsed
    total_tokens += 50
    
    output_text = bytes(output.to(torch.uint8).to("cpu").squeeze(0)).decode(errors='backslashreplace')
    
    print(f"\nPrompt {i}: '{prompt_text}'")
    print(f"Time: {elapsed:.3f}s ({50/elapsed:.1f} tokens/sec)")
    print(f"Output: {output_text[:100]}...")

print("\n" + "=" * 70)
print(f"Average: {total_time/len(prompts):.3f}s per prompt")
print(f"Total tokens: {total_tokens}")
print(f"Throughput: {total_tokens/total_time:.1f} tokens/sec")
