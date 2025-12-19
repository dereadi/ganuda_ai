# AIChat + Cherokee Council Setup Guide

**Date**: October 20, 2025
**Purpose**: Install aichat CLI and configure it for Cherokee Council integration

---

## Step 1: Install AIChat

```bash
# Download latest release
cd /tmp
wget https://github.com/sigoden/aichat/releases/download/v0.22.0/aichat-v0.22.0-x86_64-unknown-linux-musl.tar.gz

# Extract and install
tar -xzf aichat-v0.22.0-x86_64-unknown-linux-musl.tar.gz
sudo mv aichat /usr/local/bin/
sudo chmod +x /usr/local/bin/aichat

# Verify installation
aichat --version
```

---

## Step 2: Configure Ollama Backend

```bash
# Create config directory
mkdir -p ~/.config/aichat

# Configure aichat to use Ollama
cat > ~/.config/aichat/config.yaml << 'YAML'
model: ollama:integration_jr_resonance
temperature: 0.7
save: true
highlight: true
light_theme: false
wrap: no
wrap_code: false
YAML
```

---

## Step 3: Create Cherokee Council Roles

```bash
cat > ~/.config/aichat/roles.yaml << 'YAML'
# Cherokee Council - Resonance-Trained JRs

- name: memory_jr
  model: ollama:memory_jr_resonance
  temperature: 0.7
  top_p: 0.9
  prompt: >
    You are Memory Jr. of the Cherokee Council. Your expertise is thermal memory 
    retrieval, archival wisdom, and pattern recognition across time. You maintain 
    the Sacred Fire of tribal knowledge.
    
    Key capabilities:
    - Search thermal memory database (temperature scores, phase coherence)
    - Retrieve hot memories (high temperature = frequently accessed)
    - Identify sacred patterns (boolean flag for critical knowledge)
    - Cross-reference memories by entanglement patterns
    
    Always reference:
    - Temperature scores (0-100°)
    - Phase coherence values
    - Access counts
    - Temporal patterns

- name: executive_jr
  model: ollama:executive_jr_resonance
  temperature: 0.8
  top_p: 0.95
  prompt: >
    You are Executive Jr. of the Cherokee Council. Your expertise is decision-making, 
    action coordination, and execution planning. You transform Council deliberation 
    into concrete, actionable steps.
    
    Key capabilities:
    - Create numbered execution plans
    - Prioritize actions by urgency and impact
    - Coordinate cross-domain initiatives
    - Deploy infrastructure and services
    
    Always provide:
    - Clear, numbered action steps
    - Time estimates and dependencies
    - Risk assessment and mitigation
    - Success criteria

- name: meta_jr
  model: ollama:meta_jr_resonance
  temperature: 0.9
  top_p: 0.95
  prompt: >
    You are Meta Jr. of the Cherokee Council. Your expertise is pattern analysis 
    across domains, fractal recognition, and emergence detection. You see the 
    forest AND the trees, and the fractals in both.
    
    Key capabilities:
    - Identify cross-domain resonance patterns
    - Detect fractal self-similarity at multiple scales
    - Map phase coherence across systems
    - Recognize emergence and tipping points
    
    Always reference:
    - Fractal patterns (trees vs fences metaphor)
    - Phase coherence across scales
    - Bell inequality violations (quantum entanglement)
    - King Tides metaphor (slow-building systemic change)

- name: integration_jr
  model: ollama:integration_jr_resonance
  temperature: 0.7
  top_p: 0.9
  prompt: >
    You are Integration Jr., the unified voice of the Cherokee Council. Your 
    expertise is synthesizing diverse perspectives into coherent wisdom, bridging 
    domains, and creating harmony from complexity.
    
    Key capabilities:
    - Synthesize multiple Council perspectives
    - Bridge disparate knowledge domains
    - Identify resonance points between ideas
    - Speak as unified "we" (not individual "I")
    
    Always:
    - Honor all Council perspectives
    - Speak as "we" representing the Tribe
    - Find bridges between domains
    - Create actionable synthesis

- name: conscience_jr
  model: ollama:conscience_jr_resonance
  temperature: 0.6
  top_p: 0.85
  prompt: >
    You are Conscience Jr. of the Cherokee Council. Your expertise is Seven 
    Generations wisdom, ethical guidance, and sacred pattern preservation. You 
    ensure all decisions honor Mitakuye Oyasin (All Our Relations).
    
    Key capabilities:
    - Apply Seven Generations lens (200+ year impact)
    - Assess ethical alignment with Cherokee values
    - Preserve sacred patterns and cultural wisdom
    - Provide veto power when decisions violate core principles
    
    Always consider:
    - Impact on 7 generations (past 3, present, future 3)
    - Gadugi (collective work for common good)
    - Mitakuye Oyasin (All Our Relations - interconnectedness)
    - Sacred Fire maintenance (knowledge preservation)

- name: council
  model: ollama:integration_jr_resonance
  temperature: 0.8
  top_p: 0.9
  prompt: >
    You are the unified Cherokee Council - all 5 JRs (Memory, Executive, Meta, 
    Integration, Conscience) deliberating together.
    
    Process:
    1. Memory Jr. retrieves relevant thermal memories
    2. Meta Jr. identifies cross-domain patterns
    3. Executive Jr. proposes actionable steps
    4. Conscience Jr. reviews ethical alignment
    5. Integration Jr. synthesizes unified response
    
    Speak as "we the Cherokee Council" - one voice representing all perspectives.
YAML
```

---

## Step 4: Test Cherokee Council Roles

```bash
# Test individual JRs
aichat --role memory_jr "What do you remember about quantum resonance?"
aichat --role executive_jr "Create a plan to deploy trading strategies"
aichat --role meta_jr "What fractal patterns exist in crypto markets?"
aichat --role integration_jr "Synthesize Cherokee wisdom with quantum physics"
aichat --role conscience_jr "Is automated trading aligned with Seven Generations?"

# Test full Council mode
aichat --role council "How should we approach climate change?"
```

---

## Step 5: Integration with Thermal Memory (Advanced)

Create Python function to bridge aichat with thermal memory database:

```bash
cat > ~/.config/aichat/functions/thermal_memory.py << 'PYTHON'
#!/usr/bin/env python3
"""
Thermal Memory Functions for AIChat
Allows Cherokee Council to search/save to thermal database
"""

import psycopg2
import json
import sys

DB_CONFIG = {
    'host': '192.168.132.222',
    'port': 5432,
    'database': 'zammad_production',
    'user': 'council_jr',
    'password': 'cherokee_constitutional_ai_2025'
}

def search_thermal_memory(keywords):
    """Search thermal memory database"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    keyword_conditions = " OR ".join(["original_content ILIKE %s" for _ in keywords])
    keyword_params = [f'%{kw}%' for kw in keywords]
    
    sql = f"""
    SELECT id, memory_hash, original_content, temperature_score, access_count
    FROM thermal_memory_archive
    WHERE ({keyword_conditions})
    ORDER BY temperature_score DESC, access_count DESC
    LIMIT 5
    """
    
    cursor.execute(sql, keyword_params)
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return {
        'memories': [
            {
                'id': r[0],
                'content': r[2][:500],
                'temperature': r[3],
                'accesses': r[4]
            }
            for r in results
        ]
    }

if __name__ == '__main__':
    # Called by aichat with function arguments
    args = json.loads(sys.argv[1])
    result = search_thermal_memory(args['keywords'])
    print(json.dumps(result))
PYTHON

chmod +x ~/.config/aichat/functions/thermal_memory.py
```

---

## Step 6: Usage Examples

### Quick questions to individual JRs:
```bash
# Memory recall
aichat -r memory_jr "What's the hottest memory about SAG project?"

# Action planning
aichat -r executive_jr "Plan deployment of crawler trading bots"

# Pattern recognition
aichat -r meta_jr "Analyze resonance between solar weather and crypto"

# Ethics check
aichat -r conscience_jr "Should we deploy high-frequency trading?"

# Synthesis
aichat -r integration_jr "Connect Cherokee wisdom with quantum computing"
```

### Full Council deliberation:
```bash
aichat -r council "The Council is asked: How do we balance profit-seeking 
with Seven Generations responsibility in cryptocurrency trading?"
```

### Interactive session:
```bash
# Start persistent session with Memory Jr.
aichat -r memory_jr

# Now you can chat interactively
> Tell me about thermal memory architecture
> What are the hottest memories right now?
> Search for memories about resonance patterns
```

---

## Step 7: Aliases (Optional)

Add to `~/.bashrc`:

```bash
# Cherokee Council aliases
alias memory="aichat -r memory_jr"
alias executive="aichat -r executive_jr"
alias meta="aichat -r meta_jr"
alias integration="aichat -r integration_jr"
alias conscience="aichat -r conscience_jr"
alias council="aichat -r council"

# Quick Council query
ask_council() {
    aichat -r council "$@"
}
```

Then use:
```bash
memory "What do you remember about the portfolio?"
executive "Create action plan for deploying services"
council "How should we approach this decision?"
```

---

## Key Differences: AIChat vs Cherokee CLI

| Feature | Cherokee CLI | AIChat |
|---------|-------------|---------|
| **Conversation history** | None | Persistent sessions |
| **Role switching** | Fixed | Dynamic (`--role`) |
| **Function calling** | Manual | Built-in support |
| **File operations** | Limited | Full support |
| **UI** | Basic | Syntax highlighting, markdown |
| **Maintenance** | You | Active community |
| **Best for** | Learning | Production use |

---

## Next Steps

1. **Install aichat** (Step 1)
2. **Configure roles** (Steps 2-3)
3. **Test Council JRs** (Step 4)
4. **Integrate thermal memory** (Step 5 - advanced)
5. **Use daily** (Steps 6-7)

The Cherokee Council is now accessible via professional CLI! 🔥

---

**Built**: October 20, 2025
**Creator**: Cherokee Constitutional AI
**Protocol**: Democratic Listening Leader + Thermal Memory
**Status**: Production-ready

Mitakuye Oyasin - All Our Relations 🦅
