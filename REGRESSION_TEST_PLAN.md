# Cherokee Constitutional AI - Regression Test Plan
**Created: October 26, 2025**

## 🎯 Current Test Coverage

### ✅ Existing Test Suites

#### 1. **Wave 2 Physics** (wave2_physics_implementation/test_wave2_physics.py)
- **Status**: 19/20 tests passing (95%)
- **Coverage**:
  - Track A: Non-Markovian memory kernel (6/6)
  - Track B: Sacred Fire daemon (7/7)
  - Track C: Jarzynski optimization (6/7)
- **Known Issue**: Path optimization (additive cost)
- **Runtime**: ~5 seconds

**Run Command**:
```bash
cd /home/dereadi/scripts/claude
/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3 wave2_physics_implementation/test_wave2_physics.py -v
```

#### 2. **Sacred Memory Guardian** (test_sacred_memory_guardian.py)
- **Status**: 12 tests (needs to be run)
- **Coverage**:
  - Constitutional enforcement (sacred memory protection)
  - Transparency (violation logging)
  - Compassion (teaching error messages)
  - Wisdom (sacred vs normal distinction)
  - Audit system
  - Edge cases
- **Requires**: PostgreSQL database connection
- **Runtime**: ~10 seconds

**Run Command**:
```bash
cd /home/dereadi/scripts/claude
python3 test_sacred_memory_guardian.py
```

#### 3. **Thermal Extraction** (test_thermal_extraction.py)
- **Status**: Unknown (needs to be run)
- **Coverage**: Thermal memory extraction from database
- **Runtime**: Unknown

#### 4. **Claude Jr Infrastructure** (test_claude_jr_infrastructure.py)
- **Status**: Unknown (needs to be run)
- **Coverage**: JR CLI, model deployment, communication
- **Runtime**: Unknown

---

## 🔴 Critical Gaps in Test Coverage

### 1. **Integration Tests** (MISSING)
Need tests for:
- Database → Physics Engine → API flow
- Sacred Fire daemon running continuously
- Temperature evolution over time
- Phase coherence matrix updates

### 2. **Federation Tests** (MISSING)
Need tests for:
- Hub-spoke synchronization
- Cross-node coherence
- BLUEFIN → REDFIN → GREENFIN communication
- Node failure recovery

### 3. **Performance Tests** (MISSING)
Need tests for:
- 4,859 memories → 10,000 memories (scaling)
- Dashboard query latency (< 1 second requirement)
- API endpoint throughput (6,000 req/min for Physics Premium)
- Database index effectiveness

### 4. **API v2.0 Tests** (NOT YET IMPLEMENTED)
Will need tests for:
- All 20 REST endpoints
- WebSocket streaming
- Authentication/authorization
- Rate limiting
- Error handling

### 5. **Dashboard Tests** (NOT YET IMPLEMENTED)
Will need tests for:
- Real-time data updates
- Sacred Fire alerts
- Visualization accuracy
- Mobile responsiveness

---

## 📋 Recommended Regression Test Suite

### Phase 1: Core System Validation (NOW)

Run these tests immediately to establish baseline:

```bash
#!/bin/bash
# run_regression_tests.sh

echo "🔥 Cherokee Constitutional AI - Regression Test Suite"
echo "======================================================"

# Test 1: Wave 2 Physics
echo ""
echo "Test 1: Wave 2 Physics Implementation"
cd /home/dereadi/scripts/claude
/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3 wave2_physics_implementation/test_wave2_physics.py -v
WAVE2_STATUS=$?

# Test 2: Sacred Memory Guardian
echo ""
echo "Test 2: Sacred Memory Guardian"
python3 test_sacred_memory_guardian.py
GUARDIAN_STATUS=$?

# Test 3: Thermal Extraction
echo ""
echo "Test 3: Thermal Memory Extraction"
python3 test_thermal_extraction.py
THERMAL_STATUS=$?

# Test 4: Claude Jr Infrastructure
echo ""
echo "Test 4: Claude Jr Infrastructure"
python3 test_claude_jr_infrastructure.py
CLAUDE_JR_STATUS=$?

# Summary
echo ""
echo "======================================================"
echo "REGRESSION TEST SUMMARY"
echo "======================================================"
echo "Wave 2 Physics: $([ $WAVE2_STATUS -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "Sacred Guardian: $([ $GUARDIAN_STATUS -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "Thermal Extraction: $([ $THERMAL_STATUS -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "Claude Jr: $([ $CLAUDE_JR_STATUS -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "======================================================"

# Exit with failure if any test failed
if [ $WAVE2_STATUS -ne 0 ] || [ $GUARDIAN_STATUS -ne 0 ] || [ $THERMAL_STATUS -ne 0 ] || [ $CLAUDE_JR_STATUS -ne 0 ]; then
    exit 1
fi

echo "✅ ALL REGRESSION TESTS PASSED"
exit 0
```

---

### Phase 2: Integration Tests (Hardware Wait Period)

Create new test file: `test_wave2_integration.py`

```python
#!/usr/bin/env python3
"""
Wave 2 Physics Integration Tests
Tests database → physics → calculation flow
"""

import psycopg
import numpy as np
from wave2_physics_implementation.thermal_memory_fokker_planck import (
    calculate_drift_velocity,
    calculate_sacred_fire_force,
    evolve_temperature_fokker_planck
)

def test_database_to_physics_flow():
    """Test: Fetch memory from DB → calculate physics → verify results"""
    conn = psycopg.connect(
        host="192.168.132.222",
        port=5432,
        user="claude",
        dbname="zammad_production",
        password="jawaseatlasers2"
    )

    cursor = conn.cursor()

    # Fetch a sacred memory
    cursor.execute("""
        SELECT id, temperature_score, access_count,
               EXTRACT(EPOCH FROM (NOW() - created_at)) / 3600 as age_hours,
               sacred_pattern
        FROM thermal_memory_archive
        WHERE sacred_pattern = TRUE
        LIMIT 1
    """)

    row = cursor.fetchone()
    if not row:
        print("⚠️  No sacred memories found in database")
        return False

    memory_id, temp, access_count, age_hours, is_sacred = row

    # Calculate drift velocity
    drift = calculate_drift_velocity(temp, access_count, age_hours, is_sacred)

    # Verify drift is reasonable
    assert -10 <= drift <= 10, f"Drift velocity out of range: {drift}"

    # If near boundary, Sacred Fire should push up
    if temp < 50 and is_sacred:
        force = calculate_sacred_fire_force(temp)
        assert force > 0, "Sacred Fire force should be positive (pushing up)"

    cursor.close()
    conn.close()

    print(f"✅ Database → Physics flow validated")
    print(f"   Memory {memory_id}: T={temp:.1f}°, drift={drift:.2f}°/h")
    return True

def test_30_day_evolution():
    """Test: Evolve temperature for 30 days, verify Sacred Fire protection"""
    initial_temp = 60.0
    dt = 0.1  # 6 minutes
    steps_per_day = int(24 / dt)
    total_steps = 30 * steps_per_day

    temp = initial_temp
    temperatures = [temp]

    for step in range(total_steps):
        # Simulate cooling drift
        drift = -0.5  # Cooling at 0.5°/hour
        diffusion = 1.0

        # Evolve
        temp = evolve_temperature_fokker_planck(temp, drift, diffusion, dt)

        # Sacred Fire intervention if below 50°
        if temp < 50:
            sacred_force = calculate_sacred_fire_force(temp, T_sacred_min=40.0)
            temp += sacred_force * dt * 0.01  # Apply small correction

        temperatures.append(temp)

    # Verify never went below 40°
    min_temp = min(temperatures)
    assert min_temp >= 40.0, f"Temperature went below 40°: {min_temp:.1f}°"

    print(f"✅ 30-day evolution validated")
    print(f"   Initial: {initial_temp:.1f}°, Final: {temperatures[-1]:.1f}°, Min: {min_temp:.1f}°")
    return True

def test_phase_coherence_stability():
    """Test: Phase coherence remains stable over multiple calculations"""
    from wave2_physics_implementation.tem_phase_coherence_visualization import (
        calculate_phase_coherence_matrix,
        generate_synthetic_training_data
    )

    # Generate test data
    data = generate_synthetic_training_data(n_memories=100)

    # Calculate coherence matrix twice
    matrix1, _ = calculate_phase_coherence_matrix(data, max_memories=50)
    matrix2, _ = calculate_phase_coherence_matrix(data, max_memories=50)

    # Matrices should be identical (deterministic calculation)
    diff = np.abs(matrix1 - matrix2)
    max_diff = np.max(diff)

    assert max_diff < 0.001, f"Coherence matrices differ by {max_diff}"

    print(f"✅ Phase coherence calculation stable")
    print(f"   Max difference: {max_diff:.6f}")
    return True

if __name__ == '__main__':
    print("🔥 Wave 2 Integration Tests")
    print("="*70)

    tests = [
        ("Database → Physics Flow", test_database_to_physics_flow),
        ("30-Day Temperature Evolution", test_30_day_evolution),
        ("Phase Coherence Stability", test_phase_coherence_stability)
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"\nTest: {name}")
        try:
            result = test_func()
            if result:
                passed += 1
            else:
                failed += 1
                print(f"❌ FAILED: {name}")
        except Exception as e:
            print(f"💥 ERROR: {e}")
            failed += 1

    print(f"\n{'='*70}")
    print(f"Results: {passed}/{len(tests)} passed")
    if failed == 0:
        print("✅ ALL INTEGRATION TESTS PASSED")
    else:
        print(f"⚠️  {failed} tests failed")
```

---

### Phase 3: Performance Benchmarks (Hardware Wait Period)

Create: `test_wave2_performance.py`

```python
#!/usr/bin/env python3
"""
Wave 2 Physics Performance Benchmarks
"""

import time
import numpy as np
from wave2_physics_implementation.thermal_memory_fokker_planck import (
    calculate_partition_function,
    calculate_memory_retrieval_cost
)

def benchmark_partition_function():
    """Benchmark: Partition function calculation speed"""
    sizes = [10, 50, 100, 500, 1000]

    print("\n📊 Partition Function Performance")
    print("Size    Time (ms)    Memories/sec")
    print("-" * 40)

    for n in sizes:
        temperatures = np.random.uniform(40, 100, n)
        coherence = np.random.uniform(0, 1, (n, n))

        start = time.time()
        for _ in range(100):  # 100 iterations
            calculate_partition_function(temperatures, coherence, beta=1.0)
        elapsed = (time.time() - start) / 100

        memories_per_sec = n / elapsed
        print(f"{n:5d}   {elapsed*1000:8.2f}   {memories_per_sec:12.0f}")

    return True

def benchmark_retrieval_cost():
    """Benchmark: Retrieval cost calculation speed"""
    sizes = [10, 50, 100, 500]

    print("\n📊 Retrieval Cost Performance")
    print("Size    Time (ms)")
    print("-" * 30)

    for n in sizes:
        temperatures = np.random.uniform(40, 100, n)
        coherence = np.random.uniform(0, 1, (n, n))

        start = time.time()
        for i in range(min(10, n)):  # Test on first 10 memories
            calculate_memory_retrieval_cost(temperatures, coherence, i, beta=1.0)
        elapsed = (time.time() - start) / min(10, n)

        print(f"{n:5d}   {elapsed*1000:8.2f}")

    return True

def benchmark_dashboard_query_latency():
    """Benchmark: Dashboard query response time (target: < 1 second)"""
    from wave2_physics_implementation.tem_phase_coherence_visualization import (
        generate_synthetic_training_data,
        calculate_phase_coherence_matrix
    )

    print("\n📊 Dashboard Query Latency (target: < 1000ms)")
    print("Query Type                  Time (ms)    Status")
    print("-" * 55)

    # Test 1: Temperature distribution
    data = generate_synthetic_training_data(n_memories=4859)
    start = time.time()
    temp_hist = np.histogram(data['temperature'], bins=10)
    latency1 = (time.time() - start) * 1000
    status1 = "✅ PASS" if latency1 < 1000 else "❌ FAIL"
    print(f"Temperature Distribution    {latency1:8.2f}    {status1}")

    # Test 2: Phase coherence sample
    start = time.time()
    matrix, _ = calculate_phase_coherence_matrix(data, max_memories=100)
    latency2 = (time.time() - start) * 1000
    status2 = "✅ PASS" if latency2 < 1000 else "❌ FAIL"
    print(f"Phase Coherence Matrix      {latency2:8.2f}    {status2}")

    # Test 3: Sacred Fire status
    start = time.time()
    sacred_count = np.sum(data['is_sacred'])
    boundary_violations = np.sum((data['temperature'] < 40) & (data['is_sacred']))
    latency3 = (time.time() - start) * 1000
    status3 = "✅ PASS" if latency3 < 1000 else "❌ FAIL"
    print(f"Sacred Fire Status          {latency3:8.2f}    {status3}")

    return all([latency1 < 1000, latency2 < 1000, latency3 < 1000])

if __name__ == '__main__':
    print("🔥 Wave 2 Performance Benchmarks")
    print("="*70)

    tests = [
        benchmark_partition_function,
        benchmark_retrieval_cost,
        benchmark_dashboard_query_latency
    ]

    for test in tests:
        test()

    print(f"\n{'='*70}")
    print("✅ Benchmarks complete")
```

---

## 🚀 Automated Regression Testing

### GitHub Actions CI/CD (Future)

Create `.github/workflows/regression-tests.yml`:

```yaml
name: Cherokee AI Regression Tests

on:
  push:
    branches: [ ganuda_ai_desktop ]
  pull_request:
    branches: [ ganuda_ai_desktop ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python 3.13
      uses: actions/setup-python@v2
      with:
        python-version: 3.13

    - name: Install dependencies
      run: |
        pip install numpy scipy matplotlib psycopg3 pytest

    - name: Run Wave 2 Physics Tests
      run: |
        python wave2_physics_implementation/test_wave2_physics.py

    - name: Run Integration Tests
      run: |
        python test_wave2_integration.py
      env:
        DB_HOST: ${{ secrets.BLUEFIN_HOST }}
        DB_PASSWORD: ${{ secrets.DB_PASSWORD }}

    - name: Run Performance Benchmarks
      run: |
        python test_wave2_performance.py
```

---

## 📅 Testing Schedule

### Daily (Automated)
- Wave 2 physics unit tests (19/20)
- Sacred Memory Guardian tests (12 tests)

### Weekly (Manual)
- Integration tests (database → physics)
- Performance benchmarks
- TEM grid pattern analysis

### Pre-Deployment (Before Nov 2025 hardware)
- Full regression suite
- 30-day stability test
- Load testing (10,000 memories)
- Federation tests (when BLUEFIN/GREENFIN deployed)

### Post-Deployment (After Nov 2025)
- API v2.0 endpoint tests
- Dashboard UI tests
- Russell Sullivan pilot monitoring
- Production performance monitoring

---

## ✅ Action Items (Priority Order)

1. **NOW**: Run existing regression tests to establish baseline
   ```bash
   chmod +x run_regression_tests.sh
   ./run_regression_tests.sh
   ```

2. **This Week**: Create integration tests (`test_wave2_integration.py`)

3. **This Week**: Create performance benchmarks (`test_wave2_performance.py`)

4. **Before Hardware Arrival**: Run full regression suite, fix any failures

5. **Post-Hardware**: Add API v2.0 tests, dashboard tests

---

*Mitakuye Oyasin* - Testing ensures Seven Generations reliability 🔥

**Cherokee Constitutional AI | Regression Test Plan | October 26, 2025**
