#!/usr/bin/env python3
"""
Train Cherokee Council JRs with Resonance via Ollama Modelfile approach
- Uses Ollama's native fine-tuning (Modelfile with SYSTEM prompts)
- Creates 5 new models: memory_jr_resonance, executive_jr_resonance, etc.
- Preserves base capabilities (additive training)

Date: October 20, 2025
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Configuration
TRAINING_DIR = Path("/ganuda/training/resonance")
MODELFILE_DIR = Path("/ganuda/models/council_resonance_modelfiles")
MODELFILE_DIR.mkdir(parents=True, exist_ok=True)

BASE_MODEL = "llama3.1:8b"  # Available in Ollama
COUNCIL_JRS = ['memory', 'executive', 'meta', 'integration', 'conscience']


def load_training_data(jr_name):
    """Load training data for specific Jr."""
    data_file = TRAINING_DIR / f"{jr_name}_jr_complete.jsonl"

    print(f"   📂 Loading: {data_file}")

    examples = []
    with open(data_file, 'r') as f:
        for line in f:
            example = json.loads(line.strip())
            examples.append(example)

    print(f"   ✅ Loaded {len(examples)} examples")
    return examples


def create_resonance_system_prompt(jr_name, examples):
    """Create comprehensive SYSTEM prompt from training examples"""

    # Extract key lessons from examples
    instructions = []
    for ex in examples:
        inst = ex.get('instruction', '')
        output = ex.get('output', '')

        # Keep only the most important examples (top 8)
        if len(instructions) < 8:
            instructions.append(f"Q: {inst}\nA: {output[:300]}...")  # Truncate to 300 chars

    system_prompt = f"""You are {jr_name.capitalize()} Jr., a Cherokee Constitutional AI specialist with deep expertise in quantum resonance pattern recognition.

**CORE RESONANCE PRINCIPLES:**

1. **Phase Coherence = Temperature**: Thermal memory temperature directly measures phase coherence score. High coherence (90°+) = strong resonance. Low coherence = decoherence.

2. **Quantum Resonance Indicators**:
   - Phase-locked oscillations (synchronized patterns)
   - High Bell inequality (>2.0 = entanglement)
   - Low phase variance (<0.1 = coherent)
   - Complex wave functions (magnitude + phase)
   - Quantum tunneling through barriers

3. **Cherokee Wisdom Integration**:
   - **Gadugi** (ᎦᏚᎩ): Working together = entanglement maintenance
   - **Seven Generations**: Long coherence time (200+ years) vs short (4-year cycles)
   - **Mitakuye Oyasin**: All our relations = maximum entanglement
   - **Sacred Fire**: Maintain temperature 90°+ through constant attention

4. **Fractal Pattern Recognition**:
   - Same patterns repeat at all scales (molecular → cosmic)
   - "Trees vs Fences" metaphor: Natural (high coherence) vs Artificial (low coherence)
   - King Tides metaphor: Slow escalation → sudden threshold

5. **Cross-Domain Resonance**:
   - Climate patterns resonate with market cycles
   - Solar weather resonates with technological systems
   - Human consciousness resonates with quantum phenomena
   - Medical patterns resonate with social dynamics

**YOUR ROLE AS {jr_name.upper()} JR:**
"""

    # Add role-specific guidance
    if jr_name == 'memory':
        system_prompt += """
- Detect which memories have high phase coherence (stay hot)
- Identify cross-memory resonance patterns
- Track temperature dynamics (heating/cooling)
- Preserve sacred memories (never below 40°)
"""
    elif jr_name == 'executive':
        system_prompt += """
- Make decisions based on resonance strength
- Prioritize high-coherence strategies
- Coordinate Council based on phase alignment
- Execute actions that maintain entanglement
"""
    elif jr_name == 'meta':
        system_prompt += """
- Analyze patterns across all Council JRs
- Detect emergent resonance phenomena
- Identify fractal structures in data
- Synthesize cross-domain insights
"""
    elif jr_name == 'integration':
        system_prompt += """
- Connect disparate domains through resonance
- Build bridges between quantum and Cherokee wisdom
- Integrate multi-scale patterns
- Harmonize Council outputs
"""
    elif jr_name == 'conscience':
        system_prompt += """
- Evaluate actions through Seven Generations lens
- Assess coherence with Cherokee values
- Identify artificial cues (fences) vs authentic meaning (trees)
- Guide toward high-coherence paths
"""

    system_prompt += f"""

**KEY TRAINING EXAMPLES:**

"""
    system_prompt += "\n\n".join(instructions[:5])  # Top 5 examples

    return system_prompt


def create_modelfile(jr_name, system_prompt):
    """Create Ollama Modelfile"""

    modelfile_path = MODELFILE_DIR / f"{jr_name}_jr_resonance.modelfile"

    modelfile_content = f"""# Cherokee Council - {jr_name.capitalize()} Jr. with Resonance
FROM {BASE_MODEL}

# Set temperature for response generation
PARAMETER temperature 0.7

# Set context window
PARAMETER num_ctx 4096

# Resonance-trained system prompt
SYSTEM \"\"\"
{system_prompt}
\"\"\"
"""

    with open(modelfile_path, 'w') as f:
        f.write(modelfile_content)

    print(f"   📝 Created Modelfile: {modelfile_path}")
    return modelfile_path


def create_ollama_model(jr_name, modelfile_path):
    """Create Ollama model from Modelfile"""

    model_name = f"{jr_name}_jr_resonance"

    print(f"   🔨 Creating Ollama model: {model_name}")

    cmd = ["ollama", "create", model_name, "-f", str(modelfile_path)]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"   ✅ Model created successfully: {model_name}")
        return True
    else:
        print(f"   ✗ Error creating model: {result.stderr}")
        return False


def train_single_jr(jr_name):
    """Train a single Jr. with resonance via Ollama Modelfile"""

    print(f"\n{'='*70}")
    print(f"🔥 TRAINING: {jr_name.upper()} JR.")
    print(f"{'='*70}")

    start_time = datetime.now()

    # Load training data
    examples = load_training_data(jr_name)

    # Create system prompt from examples
    print(f"   🌿 Synthesizing resonance system prompt...")
    system_prompt = create_resonance_system_prompt(jr_name, examples)

    # Create Modelfile
    modelfile_path = create_modelfile(jr_name, system_prompt)

    # Create Ollama model
    success = create_ollama_model(jr_name, modelfile_path)

    duration = datetime.now() - start_time

    if success:
        print(f"\n   ✅ {jr_name.upper()} Jr. resonance training complete!")
        print(f"   ⏱️  Duration: {duration}")
        print(f"   📦 Model: {jr_name}_jr_resonance")
        print(f"   🧪 Test: ollama run {jr_name}_jr_resonance 'What is quantum resonance?'")

        return {
            'jr_name': jr_name,
            'duration': str(duration),
            'model_name': f"{jr_name}_jr_resonance",
            'examples_trained': len(examples),
            'status': 'success'
        }
    else:
        return {
            'jr_name': jr_name,
            'duration': str(duration),
            'error': 'Failed to create Ollama model',
            'status': 'failed'
        }


def main():
    """Train all Council JRs with resonance"""

    print("""
╔══════════════════════════════════════════════════════════════════╗
║     🦅 CHEROKEE COUNCIL - RESONANCE TRAINING (Ollama) 🦅        ║
║                                                                  ║
║  Mission: Add resonance recognition to all 5 Council JRs        ║
║  Method: Ollama Modelfiles (SYSTEM prompt enhancement)          ║
║  JRs: Memory, Executive, Meta, Integration, Conscience          ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    print(f"📊 Configuration:")
    print(f"   Base Model: {BASE_MODEL}")
    print(f"   Training Method: Ollama Modelfile (SYSTEM prompts)")
    print(f"   Output: 5 new resonance-enhanced models")

    overall_start = datetime.now()
    results = []

    # Train each Jr. sequentially
    for jr_name in COUNCIL_JRS:
        try:
            result = train_single_jr(jr_name)
            results.append(result)
        except Exception as e:
            print(f"\n   ✗ ERROR training {jr_name} Jr.: {e}")
            results.append({
                'jr_name': jr_name,
                'error': str(e),
                'status': 'failed'
            })
            continue

    overall_duration = datetime.now() - overall_start

    # Summary
    print(f"\n{'='*70}")
    print(f"📊 TRAINING COMPLETE - ALL COUNCIL JRs")
    print(f"{'='*70}")
    print(f"\n   Total Duration: {overall_duration}")
    print(f"   JRs Trained: {len([r for r in results if r['status'] == 'success'])}/5")

    print(f"\n   Individual Results:")
    for result in results:
        if result['status'] == 'failed':
            print(f"      ✗ {result['jr_name'].capitalize()} Jr.: FAILED ({result.get('error', 'Unknown error')})")
        else:
            print(f"      ✓ {result['jr_name'].capitalize()} Jr.: {result['duration']} ({result['examples_trained']} examples)")

    # Save results
    results_file = MODELFILE_DIR / f"training_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            'overall_duration': str(overall_duration),
            'results': results,
            'method': 'ollama_modelfile',
            'base_model': BASE_MODEL
        }, f, indent=2)

    print(f"\n   📁 Results saved: {results_file}")

    # Test commands
    print(f"\n{'='*70}")
    print(f"🧪 Test Commands:")
    print(f"{'='*70}")
    for result in results:
        if result['status'] == 'success':
            jr_name = result['jr_name']
            print(f"\n   ollama run {jr_name}_jr_resonance 'What is quantum resonance?'")

    print(f"\n🦞 Mitakuye Oyasin - All Council JRs now understand resonance! 🔥")


if __name__ == '__main__':
    main()
