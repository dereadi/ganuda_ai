# Jr Instructions: Xonsh Shell Pilot on sasass

**Priority**: 2
**Assigned Jr**: it_triad_jr
**Council Vote**: PROCEED 87%
**Pilot Node**: sasass (192.168.132.241)

---

## OBJECTIVE

Install and configure Xonsh (Python-powered shell) on sasass Mac Studio as a pilot for Federation-wide adoption. Create a custom xontrib for Cherokee AI integration.

---

### Task 1: Create Installation Script

Create `/Users/Shared/ganuda/scripts/install_xonsh.sh`:

```bash
#!/bin/bash
# Xonsh Installation Script for Cherokee AI Federation
# Target: sasass Mac Studio (macOS)
# For Seven Generations

echo "=== Cherokee AI Federation - Xonsh Installation ==="
echo "Target: $(hostname)"
echo "Date: $(date)"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

echo "Python version: $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MINOR" -lt 11 ]; then
    echo "ERROR: Xonsh requires Python 3.11+. Found $PYTHON_VERSION"
    exit 1
fi

echo "Python version OK"
echo ""

# Install xonsh with recommended extras
echo "Installing xonsh..."
pip3 install --user 'xonsh[full]'

# Verify installation
echo ""
echo "Verifying installation..."
python3 -c "import xonsh; print(f'Xonsh version: {xonsh.__version__}')"

# Create xonsh config directory
XONSH_CONFIG_DIR="$HOME/.config/xonsh"
mkdir -p "$XONSH_CONFIG_DIR"

echo ""
echo "Xonsh installed successfully!"
echo "Config directory: $XONSH_CONFIG_DIR"
echo ""
echo "To start xonsh, run: xonsh"
echo "To make it default shell: chsh -s $(which xonsh)"
```

---

### Task 2: Create Cherokee AI Xontrib

Create `/Users/Shared/ganuda/lib/xontrib_cherokee.py`:

```python
"""
xontrib-cherokee: Cherokee AI Federation Shell Integration
Provides thermal memory access, Jr queue interaction, and Council queries from xonsh.

Usage in xonsh:
    thermal_search('recursive transformers')
    jr_queue_status()
    federation_health()

For Seven Generations.
"""

import psycopg2
import json
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

def _get_db():
    """Get database connection."""
    return psycopg2.connect(**DB_CONFIG)


def thermal_search(query: str, limit: int = 5) -> list:
    """
    Search thermal memory for relevant memories.

    Usage:
        thermal_search('recursive transformers')
        thermal_search('telegram bot', limit=10)
    """
    conn = _get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, LEFT(original_content, 200) as preview,
               current_stage, temperature_score, created_at
        FROM thermal_memory_archive
        WHERE original_content ILIKE %s
        ORDER BY temperature_score DESC, created_at DESC
        LIMIT %s
    """, (f'%{query}%', limit))

    results = cur.fetchall()
    cur.close()
    conn.close()

    print(f"\n🔥 Thermal Memory Search: '{query}' ({len(results)} results)\n")
    print("-" * 80)

    for r in results:
        print(f"[{r[0]}] {r[2]} (temp: {r[3]})")
        print(f"    {r[1]}...")
        print()

    return results


def thermal_write(content: str, stage: str = 'WHITE_HOT', score: int = 95) -> int:
    """
    Write a new memory to thermal memory archive.

    Usage:
        thermal_write('Important finding about...')
        thermal_write('Less important note', stage='WARM', score=70)
    """
    import hashlib

    conn = _get_db()
    cur = conn.cursor()

    memory_hash = hashlib.md5(f"{content}_{datetime.now()}".encode()).hexdigest()

    cur.execute("""
        INSERT INTO thermal_memory_archive
        (memory_hash, original_content, current_stage, temperature_score)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (memory_hash, content, stage, score))

    memory_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    print(f"🔥 Memory stored: ID {memory_id} ({stage}, temp: {score})")
    return memory_id


def jr_queue_status() -> list:
    """
    Show current Jr work queue status.

    Usage:
        jr_queue_status()
    """
    conn = _get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT task_id, title, assigned_jr, priority, status,
               TO_CHAR(created_at, 'MM-DD HH24:MI') as created
        FROM jr_work_queue
        WHERE status IN ('pending', 'in_progress')
        ORDER BY priority, created_at
        LIMIT 10
    """)

    results = cur.fetchall()
    cur.close()
    conn.close()

    print(f"\n📋 Jr Work Queue ({len(results)} active tasks)\n")
    print("-" * 90)
    print(f"{'ID':<10} {'Title':<40} {'Jr':<15} {'P':>2} {'Status':<12}")
    print("-" * 90)

    for r in results:
        print(f"{r[0][:8]:<10} {r[1][:38]:<40} {r[2]:<15} {r[3]:>2} {r[4]:<12}")

    return results


def jr_queue_add(title: str, instruction_file: str, priority: int = 2,
                 assigned_jr: str = 'it_triad_jr') -> str:
    """
    Add a task to the Jr work queue.

    Usage:
        jr_queue_add('Fix the bug', '/ganuda/docs/jr_instructions/JR_FIX_BUG.md')
        jr_queue_add('Urgent task', '/path/to/instructions.md', priority=1)
    """
    import hashlib

    conn = _get_db()
    cur = conn.cursor()

    task_id = hashlib.md5(f"{title}_{datetime.now()}".encode()).hexdigest()

    cur.execute("""
        INSERT INTO jr_work_queue
        (task_id, title, assigned_jr, priority, status, instruction_file, created_at)
        VALUES (%s, %s, %s, %s, 'pending', %s, NOW())
        RETURNING task_id
    """, (task_id, title, assigned_jr, priority, instruction_file))

    conn.commit()
    cur.close()
    conn.close()

    print(f"📋 Task queued: {task_id[:8]}... ({title})")
    return task_id


def federation_health() -> dict:
    """
    Check Federation cluster health.

    Usage:
        federation_health()
    """
    import subprocess

    nodes = {
        'redfin': '192.168.132.223',
        'bluefin': '192.168.132.222',
        'greenfin': '192.168.132.224',
        'sasass': '192.168.132.241',
        'sasass2': '192.168.132.242'
    }

    print("\n🏔️ Cherokee AI Federation Health\n")
    print("-" * 50)

    results = {}
    for name, ip in nodes.items():
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '1', ip],
                capture_output=True, timeout=2
            )
            status = '✓ UP' if result.returncode == 0 else '✗ DOWN'
        except:
            status = '? UNKNOWN'

        results[name] = status
        print(f"  {name:<12} ({ip}): {status}")

    print("-" * 50)
    return results


def msp_score() -> dict:
    """
    Calculate current MSP (Maximum Sustained Power) score.

    Usage:
        msp_score()
    """
    conn = _get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT current_stage, COUNT(*)
        FROM thermal_memory_archive
        GROUP BY current_stage
    """)

    stages = dict(cur.fetchall())
    cur.close()
    conn.close()

    # MSP = (persistent + slow_decay) / (fast_decay + 1)
    persistent = stages.get('WHITE_HOT', 0) + stages.get('RED_HOT', 0)
    slow_decay = stages.get('HOT', 0) + stages.get('WARM', 0)
    fast_decay = stages.get('COOL', 0) + stages.get('COLD', 0) + stages.get('ARCHIVE', 0)

    msp = round((persistent + slow_decay) / (fast_decay + 1), 2)

    print(f"\n⚡ MSP Score: {msp}")
    print(f"   Persistent (WHITE_HOT + RED_HOT): {persistent}")
    print(f"   Slow Decay (HOT + WARM): {slow_decay}")
    print(f"   Fast Decay (COOL + COLD + ARCHIVE): {fast_decay}")
    print()

    return {'msp': msp, 'stages': stages}


# Register functions in xonsh namespace
def _load_xontrib_(xsh, **kwargs):
    """Load the Cherokee AI xontrib."""
    xsh.ctx['thermal_search'] = thermal_search
    xsh.ctx['thermal_write'] = thermal_write
    xsh.ctx['jr_queue_status'] = jr_queue_status
    xsh.ctx['jr_queue_add'] = jr_queue_add
    xsh.ctx['federation_health'] = federation_health
    xsh.ctx['msp_score'] = msp_score

    print("🪶 Cherokee AI xontrib loaded. For Seven Generations.")
    print("   Commands: thermal_search(), thermal_write(), jr_queue_status(),")
    print("             jr_queue_add(), federation_health(), msp_score()")
```

---

### Task 3: Create Xonsh RC File

Create `/Users/Shared/ganuda/config/xonshrc`:

```python
# Cherokee AI Federation - Xonsh Configuration
# For Seven Generations

# ============================================
# ENVIRONMENT
# ============================================
$XONSH_SHOW_TRACEBACK = True
$XONSH_HISTORY_SIZE = (10000, 'commands')
$XONSH_HISTORY_BACKEND = 'sqlite'

# Federation paths
$GANUDA_HOME = '/Users/Shared/ganuda'
$PATH.insert(0, $GANUDA_HOME + '/scripts')
$PATH.insert(0, $GANUDA_HOME + '/bin')

# ============================================
# PROMPT
# ============================================
$PROMPT = '{env_name}{BOLD_GREEN}{user}@{hostname}{RESET}:{BOLD_BLUE}{cwd}{RESET}🪶 '
$RIGHT_PROMPT = '{gitstatus}'

# ============================================
# ALIASES
# ============================================
aliases['ll'] = 'ls -la'
aliases['gs'] = 'git status'
aliases['gd'] = 'git diff'

# Federation shortcuts
aliases['redfin'] = 'ssh dereadi@192.168.132.223'
aliases['bluefin'] = 'ssh dereadi@192.168.132.222'
aliases['greenfin'] = 'ssh dereadi@192.168.132.224'

# Jr shortcuts
aliases['jrs'] = 'jr_queue_status'
aliases['thermal'] = 'thermal_search'
aliases['health'] = 'federation_health'
aliases['msp'] = 'msp_score'

# ============================================
# LOAD CHEROKEE XONTRIB
# ============================================
import sys
sys.path.insert(0, '/Users/Shared/ganuda/lib')

try:
    from xontrib_cherokee import (
        thermal_search, thermal_write,
        jr_queue_status, jr_queue_add,
        federation_health, msp_score
    )
    print("🪶 Cherokee AI Federation Shell")
    print("   Node: " + $(hostname).strip())
    print("   Commands: thermal, jrs, health, msp")
    print()
except Exception as e:
    print(f"Warning: Could not load Cherokee xontrib: {e}")

# ============================================
# STARTUP
# ============================================
# Show quick health on startup
# federation_health()
```

---

### Task 4: Create Setup Script

Create `/Users/Shared/ganuda/scripts/setup_xonsh_cherokee.sh`:

```bash
#!/bin/bash
# Setup Xonsh with Cherokee AI Integration
# Run this after install_xonsh.sh

echo "=== Cherokee AI - Xonsh Configuration Setup ==="

GANUDA_HOME="/Users/Shared/ganuda"
XONSH_CONFIG="$HOME/.config/xonsh"

# Create config directory
mkdir -p "$XONSH_CONFIG"

# Link or copy xonshrc
if [ -f "$GANUDA_HOME/config/xonshrc" ]; then
    cp "$GANUDA_HOME/config/xonshrc" "$HOME/.xonshrc"
    echo "✓ Copied xonshrc to ~/.xonshrc"
else
    echo "✗ xonshrc not found at $GANUDA_HOME/config/xonshrc"
fi

# Verify xontrib
if [ -f "$GANUDA_HOME/lib/xontrib_cherokee.py" ]; then
    echo "✓ Cherokee xontrib found"
else
    echo "✗ Cherokee xontrib not found"
fi

# Test xonsh
echo ""
echo "Testing xonsh..."
xonsh -c "print('Xonsh is working!'); from xontrib_cherokee import msp_score; msp_score()"

echo ""
echo "Setup complete!"
echo ""
echo "To start xonsh: xonsh"
echo "To test Cherokee integration: thermal_search('test')"
```

---

## SUCCESS CRITERIA

1. install_xonsh.sh runs without errors on sasass
2. xontrib_cherokee.py loads successfully
3. thermal_search() returns results from bluefin
4. jr_queue_status() shows current queue
5. federation_health() pings all nodes
6. msp_score() calculates current MSP

---

## PILOT METRICS TO TRACK

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Startup time | < 2 seconds | `time xonsh -c exit` |
| Memory usage | < 100MB | `ps aux | grep xonsh` |
| Command latency | < 50ms | Subjective feel |
| Python integration | Seamless | Can run Python inline |

---

## ROLLOUT PLAN

1. **Week 1**: Pilot on sasass
2. **Week 2**: Evaluate, fix issues
3. **Week 3**: Extend to sasass2
4. **Week 4**: Linux nodes (redfin, bluefin, greenfin)
5. **Week 5**: Document and standardize

---

*For Seven Generations - Cherokee AI Federation*
