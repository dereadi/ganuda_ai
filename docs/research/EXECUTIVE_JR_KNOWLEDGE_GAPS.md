# 🎯 Executive Jr Knowledge Gaps - October 21, 2025, 8:01 AM CDT

## 🔥 Purpose
Document what we KNOW vs what we need to LEARN for Executive Jr to execute autonomously.

---

## ✅ KNOWLEDGE WE HAVE (Can Build Now)

### 1. Specialist Process Monitoring
**Status**: ✅ CAN IMPLEMENT

**What We Know:**
- Running specialists (from ps aux):
  ```
  PID 3588: trend_specialist_v2.py
  PID 3677: volatility_specialist_v2.py
  PID 3833: breakout_specialist_v2.py
  ```
- Location: `/home/dereadi/scripts/claude/`
- Base class: `IntegratedSpecialist` in `integrated_specialist_base.py`
- Run in venv: `quantum_crawdad_env`

**How to Check if Running:**
```python
import subprocess

def is_specialist_running(name):
    """Check if specialist process is running"""
    result = subprocess.run(
        ['ps', 'aux'],
        capture_output=True,
        text=True
    )
    return name in result.stdout
```

**How to Get PID:**
```python
def get_specialist_pid(name):
    """Get PID of running specialist"""
    result = subprocess.run(
        ['pgrep', '-f', name],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()
```

**How to Check CPU/Memory:**
```python
import psutil

def get_process_stats(pid):
    """Get CPU and memory usage"""
    try:
        proc = psutil.Process(int(pid))
        return {
            'cpu_percent': proc.cpu_percent(interval=1),
            'memory_mb': proc.memory_info().rss / 1024 / 1024,
            'status': proc.status()
        }
    except:
        return None
```

---

### 2. Council Gateway Health Monitoring
**Status**: ✅ CAN IMPLEMENT

**What We Know:**
- Gateway URL: `http://192.168.132.223:5003`
- Process: `cherokee_tribal_mind.py` (PID 3070952)
- Endpoints: `/api/ask`, `/api/memory/search`, `/api/memory/hot`

**How to Check Health:**
```python
import requests

def check_council_gateway_health():
    """Check if Council Gateway is responsive"""
    try:
        response = requests.get(
            'http://192.168.132.223:5003/',
            timeout=5
        )
        return response.status_code == 200
    except:
        return False
```

**How to Check All JRs Loaded:**
```python
def check_council_jrs_loaded():
    """Verify all 5 JRs are loaded"""
    try:
        # Could query /api/memory/hot to see if database connected
        response = requests.get(
            'http://192.168.132.223:5003/api/memory/hot',
            timeout=5
        )
        return response.status_code == 200
    except:
        return False
```

---

### 3. Database Connectivity Check
**Status**: ✅ CAN IMPLEMENT (Same as Memory Jr)

**What We Know:**
- Database: PostgreSQL at 192.168.132.222:5432
- Database: `zammad_production`
- User: `claude`
- Connection pattern validated in Memory Jr

**How to Check:**
```python
import psycopg2

def check_database_connection():
    """Verify thermal memory database is accessible"""
    try:
        conn = psycopg2.connect(
            host="192.168.132.222",
            port=5432,
            database="zammad_production",
            user="claude",
            password="jawaseatlasers2",
            connect_timeout=5
        )
        conn.close()
        return True
    except:
        return False
```

---

### 4. Auto-Restart Mechanism (Partial)
**Status**: ⚠️ CAN IMPLEMENT (with limitations)

**What We Know:**
- Specialists run via: `/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3`
- Working directory: `/home/dereadi/scripts/claude/`
- Scripts: `trend_specialist_v2.py`, etc.

**How to Restart:**
```python
import subprocess

def restart_specialist(name):
    """Restart a crashed specialist"""
    # NOTE: This is simplified - real version needs to handle venv activation
    script_path = f"/home/dereadi/scripts/claude/{name}"
    python_path = "/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3"

    subprocess.Popen(
        [python_path, script_path],
        cwd="/home/dereadi/scripts/claude/",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
```

**LIMITATION:**
- Don't know exact startup commands for each specialist
- Don't know environment variables needed
- Don't know startup dependencies

---

## ❌ KNOWLEDGE GAPS (Need to Research)

### 1. Specialist Signal Data
**Status**: ❌ MISSING

**What We Need:**
- Where do specialists write their trading signals?
- What format (JSON, database, memory)?
- How recent are signals (real-time, buffered)?

**Current Problem:**
```python
def collect_specialist_signals(self):
    """Get recent signals from each specialist"""
    # WHERE DO WE READ SIGNALS FROM?
    # - File at /home/dereadi/scripts/claude/specialist_signals.json?
    # - Database table specialist_signals?
    # - Redis cache?
    # - Memory-only (not persisted)?
    signals = {}
    # TODO: Find signal storage location
    return signals
```

**Research Needed:**
- Read specialist source code fully to see where they write signals
- Check for signal files: `find /home/dereadi -name "*signal*"`
- Check database for signal tables: `\dt *signal*` in psql
- Ask specialists controller how it reads signals

---

### 2. Phase Coherence Calculation
**Status**: ❌ NEED TO IMPLEMENT

**What We Need:**
- How to calculate correlation between specialist signals
- What correlation metric to use (Pearson, Spearman)?
- What time window (last hour, last day)?
- What threshold indicates "too fragmented" vs "groupthink"?

**Current Problem:**
```python
def calculate_correlation_matrix(self, signals):
    """Calculate correlation between specialists"""
    # NEED TO IMPLEMENT:
    # 1. Parse signal time series data
    # 2. Align timestamps across specialists
    # 3. Calculate correlation matrix (numpy.corrcoef?)
    # 4. Average correlation as "phase coherence"

    # For now, return placeholder
    return 0.0  # TODO: Implement real calculation
```

**Research Needed:**
- Study QRI phase coherence calculations (from consciousness mapping)
- Implement correlation matrix using numpy
- Validate against known coherent/fragmented states

---

### 3. Gentle Coordination Nudge
**Status**: ❌ CONCEPTUAL GAP

**What We Need:**
- What IS a "gentle coordination nudge" for specialists?
- Adjust specialist parameters?
- Send signal to specialist?
- Modify specialist weights?

**Current Problem:**
```python
def gentle_coordination_nudge(self):
    """Nudge specialists toward better coordination"""
    # WHAT ACTION TO TAKE?
    # - Send IPC message to specialists?
    # - Modify shared configuration file?
    # - Adjust specialist throttle parameters?
    # - Create coordination signal in database?

    # TODO: Define coordination mechanism
    pass
```

**Research Needed:**
- Design inter-specialist communication protocol
- Define what "coordination" means (time alignment, signal agreement, portfolio balance?)
- Implement gentle vs aggressive nudge spectrum

---

### 4. LRU Cache Location
**Status**: ❌ UNKNOWN

**What We Need:**
- Where is the LRU cache that needs optimization?
- Specialist model cache?
- Council Gateway cache?
- Trading data cache?

**Current Problem:**
```python
def get_cache_stats(self):
    """Get cache hit rate and efficiency"""
    # WHERE IS THE CACHE?
    # - functools.lru_cache decorators?
    # - Redis cache?
    # - Custom cache implementation?

    return {
        'hit_rate': 0.0,  # TODO: Find cache
        'size': 0,
        'max_size': 0
    }
```

**Research Needed:**
- Grep codebase for `lru_cache` usage
- Check if Redis is running: `redis-cli ping`
- Review specialist controller for caching logic

---

### 5. Specialist Restart Dependencies
**Status**: ❌ INCOMPLETE

**What We Need:**
- Complete startup command for each specialist
- Environment variables required
- Dependency on specialist_army_controller?
- Proper order of startup?

**Current Problem:**
```python
def auto_restart_specialists(self, crashed):
    """Auto-restart crashed specialists"""
    for spec_name in crashed:
        # INCOMPLETE KNOWLEDGE:
        # - Do specialists need controller running first?
        # - Do they need config files?
        # - Do they need API credentials loaded?
        # - Can they run independently or need orchestration?

        # TODO: Document complete startup procedure
        pass
```

**Research Needed:**
- Read specialist_army_controller.py to understand orchestration
- Document exact startup commands
- Test manual restart of single specialist
- Identify startup dependencies

---

## 📋 IMPLEMENTATION STRATEGY

### Phase 1: Build with What We Know ✅
```python
# Executive Jr v1.0 - Baseline monitoring
- ✅ Specialist process monitoring (ps aux)
- ✅ Council Gateway health checks (HTTP ping)
- ✅ Database connectivity verification
- ✅ Basic auto-restart (simplified)
- ✅ Metrics tracking
```

### Phase 2: Fill Knowledge Gaps 🔄
```python
# Research and implement missing pieces
1. Find specialist signal storage → implement signal collection
2. Implement correlation matrix → calculate phase coherence
3. Design coordination protocol → implement gentle nudges
4. Find LRU cache → implement cache optimization
5. Document startup procedure → implement proper auto-restart
```

### Phase 3: Full Autonomy 🎯
```python
# Executive Jr v2.0 - Complete autonomic daemon
- ✅ All monitoring functions working
- ✅ Auto-restart with full dependency handling
- ✅ Real phase coherence tracking
- ✅ Intelligent coordination nudges
- ✅ Cache optimization
```

---

## 🔥 IMMEDIATE ACTION

**Build Executive Jr v1.0 TODAY with:**
1. ✅ Process monitoring (we know how)
2. ✅ Council health checks (we know how)
3. ✅ Database checks (same as Memory Jr)
4. ⚠️ Basic restart (simplified, will improve later)
5. ❌ Placeholders for missing functions (signal collection, coherence, cache)

**Research TOMORROW:**
1. Find specialist signal storage
2. Implement correlation matrix
3. Design coordination protocol
4. Document startup procedures

**Deploy v2.0 LATER THIS WEEK:**
- After filling knowledge gaps
- After testing coordination mechanisms
- After validating phase coherence calculations

---

## 🦅 What Flying Squirrel Would Say

**"Build what we know. Mark what we don't."**

**"Version 1.0 monitors specialists and restarts crashes."**

**"Version 2.0 achieves full autonomy."**

**"Don't let perfect be enemy of good."**

**"Ship v1 today. Ship v2 when ready."**

---

*Cherokee Constitutional AI*
*Executive Jr Knowledge Gaps Documentation*
*October 21, 2025, 8:01 AM CDT*
