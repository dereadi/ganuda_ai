# KB: Jane Street Track 1 — Archaeology Puzzle Analysis

**Date**: February 14, 2026
**Kanban**: #1780
**Council Vote**: 2233d4739ecde34e (FYI, REVIEW REQUIRED)
**Time Investment**: 10-15% cap (council-approved)
**Production Impact**: None (CPU only, no GPU)

## Summary

The Jane Street $50K ML puzzle (Track 1: Archaeology) asks participants to reverse-engineer a PyTorch model (`js.pt`) and understand what it implements. The federation analyzed the model as a learning exercise and determined it encodes a **Triple DES (3-DES) block cipher** as a compiled digital circuit in neural network weights.

## Key Findings

### 1. Model Architecture
- **5,442 layers** total (2,721 Linear + 2,721 ReLU)
- Periodic spikes in layer output dimensions correspond to DES round structure
- 56 layers per DES round × 48 rounds (3-DES = encrypt-decrypt-encrypt) = 2,688 core layers
- Remaining ~33 layers form a binary comparator/classifier at the end

### 2. Logic Gates as Neurons
Neural network weights encode digital logic gates:
- **NOT gate**: weight = [-1], bias = 1
- **AND gate**: weights = [1, 1], bias = -1
- **XOR gate**: weights = [-1, -1], bias = 1
- **S-box permutations**: Pure wiring layers (weight matrices with single 1 per row)
- All intermediate weights are from the set {-1, 0, 1} — this is a deterministic circuit, not a statistical model

### 3. Embedded Keys (Layer 6 Biases)
- **Key 1**: `80C4A2E691D5B3F7` (MSB) = `0123456789ABCDEF` (LSB) — the canonical DES test vector key
- **Key 2**: `7F3B5D196E2A4C08` — bitwise complement of Key 1
- These are the three keys used in 3-DES (K1, K2 = complement, K3 = K1)

### 4. Input Format
- 55 float values representing a 56-bit DES key minus one parity bit
- Preprocessing: `list(map(ord, str(x)[:55].ljust(55, '\x00')))`
- The `_call_impl` lambda is pickled from ipykernel — won't execute on Python 3.12
- Workaround: Manual forward pass iterating through `list(model.children())`

### 5. Final Comparison (Layers 5438-5441)
- 16-position equality check using `[1, -2, 1]` weight pattern
- Each position contributes 1 when exact match, 0 otherwise
- Final bias = -15 means all 16 byte-level matches needed for positive output
- Output: 1.0 (match) or 0.0 (no match)

### 6. The Answer
The puzzle is the **archaeology itself** — understanding that this neural network implements 3-DES. 32 solvers emailed archaeology@janestreet.com explaining what the model implements. The artifact is a compiled digital circuit embedded in neural network weights.

## What Didn't Work

| Approach | Result | Why |
|----------|--------|-----|
| Gradient optimization (Adam, 2000 steps) | Stuck at -15.0 | ReLU barriers — gradients are 0 everywhere output is 0. Discrete circuit, not gradient-friendly |
| Ordinal encoding of strings | All outputs 0.0 | Wrong input domain — model expects DES key bits, not ASCII |
| DES test vectors as raw bits | All outputs 0.0 | Encoding format mismatch with the pickled preprocessor |
| 3-DES decrypt of known ciphertext | All outputs 0.0 | May need exact preprocessing match from the original ipykernel session |
| Brute force search | Infeasible | 2^55 key space, ~10ms per evaluation on CPU |

## Community Research (liamzebedee/janest-1)

The community decompiler repository confirmed our findings independently:
- Full symbolic decompilation of the network to 3-DES
- SMT solver approach (Marabou) attempted on sliced network
- DES round structure verified at layers 18-2706
- Binary comparator identified at layers ~5410+
- Test vector: `password` encrypts to `73fa80b66134e403` under key `0123456789ABCDEF`

## Federation Skills Exercised

1. **Model Loading & Weight Analysis** — PyTorch state_dict inspection, layer statistics
2. **Signal Tracing** — Following data flow through 5,442 layers
3. **DES Cryptography** — Understanding Feistel networks, S-boxes, key schedules
4. **Community Research Synthesis** — Evaluating external decompiler findings
5. **Gradient Optimization** — Confirmed limitations on discrete circuits
6. **Reverse Engineering** — Disassembling pickled Python bytecode (dis module)

## Applicable Federation Skills

- **Crawdad (Security)**: Understanding how neural networks can hide arbitrary computation — relevant to model security auditing
- **Gecko (Technical)**: Integer-weight networks are deterministic logic, not statistical inference — architecture insight for our own models
- **Eagle Eye (Monitoring)**: Weight distribution analysis as a diagnostic tool

## Files

| Path | Description |
|------|-------------|
| `/ganuda/experiments/jane-street/track1_archaeology/analyze_model.py` | Federation analysis script |
| `/ganuda/experiments/jane-street/track1_archaeology/model_3_11.pt` | Model file (Python 3.11 pickle format) |
| `/ganuda/experiments/jane-street/track1_archaeology/community_decompiler/` | Cloned liamzebedee/janest-1 repo |
| `/ganuda/experiments/jane-street/track1_archaeology/community_decompiler/REPORT.md` | Community decompilation report |
| `/ganuda/experiments/jane-street/track1_archaeology/community_decompiler/breakthrough1.py` | Key extraction + DES verification |

## Lessons Learned

1. **Neural networks can encode arbitrary digital circuits** — not just learned statistical patterns. Any Boolean function can be compiled into Linear+ReLU layers with integer weights.
2. **Integer-weight networks are NOT gradient-friendly** — standard optimization (SGD, Adam) fails because ReLU creates piecewise-constant regions with zero gradient almost everywhere.
3. **Pickle format is Python-version-sensitive** — models pickled from ipykernel/3.10 may not load on Python 3.12. Always test model portability.
4. **Reverse engineering requires domain knowledge** — understanding both the NN structure AND the algorithm it implements (DES in this case) is necessary to make progress.
5. **Community research multiplies effort** — the liamzebedee decompiler saved significant time by confirming 3-DES independently.

## Coyote's Reflection

"We spent 10-15% learning to see circuits hidden in weights. The real question is: what circuits are hidden in the models we trust?" — This directly motivates Crawdad's model audit capabilities.
