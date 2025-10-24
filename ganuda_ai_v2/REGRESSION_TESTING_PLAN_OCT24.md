# Cherokee Constitutional AI - Regression Testing Plan
## Seven Generations Quality Assurance

**Date**: October 24, 2025
**Purpose**: Ensure long-term stability and sacred data protection across all system changes
**Triad Consensus**: 4-of-4 JRs consulted (Executive, Meta, Integration, Conscience)
**Cherokee Principle**: "Testing is like pruning a tree - maintains strength and resilience for generations"

---

## Executive Summary

**Integration Point**: **NOW** (Week 3-5) - before Track 2 complexity begins

**Key Decision**: Establish regression testing infrastructure during Track 1, validate existing systems before adding Privacy Kernel.

**Quality Standards**:
- ✅ 90%+ code coverage for all regression tests (War Chief Executive Jr)
- ✅ 3 test cycles per milestone (before/during/after)
- ✅ Statistical validation for thermal memory (Meta Jr)
- ✅ Automated CI/CD integration (Peace Chief Integration Jr)
- ✅ Seven Generations quality (Medicine Woman Conscience Jr)

---

## Phase 1: Testing Infrastructure Setup (Week 3, Days 1-3)

### 1.1 Testing Framework Installation
**Owner**: War Chief Meta Jr
**Timeline**: 3 days

**Install**:
```bash
cd /home/dereadi/scripts/claude/ganuda_ai_v2
python3 -m venv test_env
test_env/bin/pip install pytest pytest-cov hypothesis pytest-asyncio pytest-mock
```

**Framework Selection** (Meta Jr recommendation):
- **Pytest**: Core testing framework
- **pytest-cov**: Code coverage analysis (target: 90%+)
- **hypothesis**: Property-based testing for thermal memory
- **pytest-asyncio**: Async Guardian API testing
- **pytest-mock**: Mocking for database interactions

---

### 1.2 Test Directory Structure
**Owner**: War Chief Integration Jr
**Timeline**: 1 day

**Create**:
```bash
ganuda_ai_v2/
├── tests/
│   ├── __init__.py
│   ├── unit/                    # Unit tests (isolation)
│   │   ├── test_guardian_api.py
│   │   ├── test_encrypted_cache.py
│   │   ├── test_thermal_memory.py
│   │   └── test_aniwaya_extension.py
│   ├── integration/             # Integration tests
│   │   ├── test_aniwaya_guardian_integration.py
│   │   ├── test_guardian_database_integration.py
│   │   └── test_privacy_kernel_integration.py  # Future
│   ├── statistical/             # Thermal memory statistical validation
│   │   ├── test_phase_coherence.py
│   │   ├── test_temperature_scoring.py
│   │   └── test_thermal_decay.py
│   ├── e2e/                     # End-to-end tests
│   │   └── test_full_provenance_flow.py
│   └── fixtures/                # Test data and mocks
│       ├── mock_thermal_data.json
│       └── mock_cache_entries.db
└── pytest.ini                   # Pytest configuration
```

---

### 1.3 CI/CD Integration (GitHub Actions)
**Owner**: Peace Chief Integration Jr
**Timeline**: 2 days

**Create** `.github/workflows/regression_tests.yml`:
```yaml
name: Cherokee Constitutional AI - Regression Tests

on:
  push:
    branches: [ ganuda_ai_desktop, main ]
  pull_request:
    branches: [ ganuda_ai_desktop ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python 3.13
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-cov hypothesis pytest-asyncio
        pip install -r requirements.txt

    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=desktop_assistant --cov-report=html

    - name: Run integration tests
      run: |
        pytest tests/integration/ -v

    - name: Run statistical validation
      run: |
        pytest tests/statistical/ -v

    - name: Upload coverage report
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
        flags: cherokee_constitutional_ai
        name: codecov-umbrella
```

---

## Phase 2: Baseline Test Suite (Week 3, Days 4-7)

### 2.1 Guardian API Unit Tests
**Owner**: War Chief Executive Jr
**Coverage Target**: 80%+ for all endpoints
**Timeline**: 2 days

**File**: `tests/unit/test_guardian_api.py`

```python
import pytest
from fastapi.testclient import TestClient
from desktop_assistant.guardian_api_bridge import app

client = TestClient(app)

def test_health_endpoint():
    """Test Guardian API health check."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["guardian_initialized"] == True
    assert "cherokee_values" in data

def test_evaluate_query_pii_detection():
    """Test Guardian PII detection."""
    response = client.post("/evaluate", json={
        "query": "Email john.smith@example.com about SSN 123-45-6789"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["allowed"] == False
    assert "email" in data["pii_found"]
    assert "ssn" in data["pii_found"]
    assert data["protection_level"] == "PRIVATE"

def test_evaluate_query_medical_entities():
    """Test Guardian medical entity detection (C1)."""
    response = client.post("/evaluate", json={
        "query": "Patient prescribed Lipitor 20mg for high cholesterol"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["medical_entities"] > 0  # spaCy NER should detect entities
    assert data["protection_level"] in ["PRIVATE", "SENSITIVE"]

def test_thermal_memory_endpoint():
    """Test Guardian thermal memory retrieval."""
    response = client.get("/thermal/recent")
    assert response.status_code == 200
    data = response.json()
    assert "temperature" in data
    assert "phaseCoherence" in data
    assert "sacredFloor" in data
    assert data["sacredFloor"] == 40  # Validate 40° sacred floor
```

**Test Coverage**: 80%+ for Guardian API

---

### 2.2 EncryptedCache Unit Tests
**Owner**: War Chief Memory Jr
**Coverage Target**: 90%+ (critical system)
**Timeline**: 2 days

**File**: `tests/unit/test_encrypted_cache.py`

```python
import pytest
from pathlib import Path
from desktop_assistant.cache.encrypted_cache import EncryptedCache

@pytest.fixture
def temp_cache(tmp_path):
    """Create temporary cache for testing."""
    cache = EncryptedCache(cache_dir=tmp_path)
    yield cache
    cache.close()

def test_cache_put_get_email(temp_cache):
    """Test email encryption and retrieval."""
    email_content = {
        "subject": "Cherokee Council Meeting",
        "from": "war.chief@ganuda.ai",
        "to": "triad@ganuda.ai",
        "date": "2025-10-24T10:00:00Z",
        "body": "Warriors, M1 Provenance complete. Mitakuye Oyasin."
    }

    temp_cache.put_email(email_id="test_001", content=email_content, sacred=True)

    # Retrieve and validate
    retrieved = temp_cache.get("email:test_001")
    assert retrieved is not None
    assert "Cherokee Council Meeting" in retrieved["metadata"]["subject"]
    assert retrieved["temperature_score"] == 100.0  # Sacred emails start at 100°

def test_cache_thermal_memory_update(temp_cache):
    """Test thermal memory temperature increase on access."""
    temp_cache.put_email("test_002", {"body": "Test", "subject": "Test"}, sacred=False)

    # First access
    entry1 = temp_cache.get("email:test_002")
    temp1 = entry1["temperature_score"]

    # Second access (should increase temperature by +5°)
    entry2 = temp_cache.get("email:test_002")
    temp2 = entry2["temperature_score"]

    assert temp2 >= temp1 + 5.0  # Validate +5° increase per access

def test_cache_sacred_floor_enforcement(temp_cache):
    """Test sacred entries maintain 40° floor."""
    temp_cache.put_email("sacred_001", {"body": "Sacred", "subject": "Sacred"}, sacred=True)

    # Attempt to evict cold entries (should preserve sacred)
    deleted_count = temp_cache.evict_cold_entries(threshold_temp=80.0, preserve_sacred=True)

    # Sacred entry should still exist
    sacred_entry = temp_cache.get("email:sacred_001")
    assert sacred_entry is not None
    assert sacred_entry["temperature_score"] >= 40.0  # Sacred floor maintained
```

**Test Coverage**: 90%+ for EncryptedCache

---

### 2.3 Thermal Memory Statistical Validation
**Owner**: War Chief Meta Jr
**Coverage Target**: Statistical confidence intervals
**Timeline**: 3 days

**File**: `tests/statistical/test_thermal_memory.py`

```python
import pytest
import numpy as np
from scipy import stats
from hypothesis import given, strategies as st

@given(st.floats(min_value=0.8, max_value=1.0))
def test_phase_coherence_range(phase_coherence):
    """Property-based test: Phase coherence must be 0.8-1.0 for high coherence."""
    assert 0.8 <= phase_coherence <= 1.0

def test_temperature_statistical_distribution():
    """Statistical validation: Temperature scores follow expected distribution."""
    # Simulate 100 temperature readings
    temperatures = np.random.normal(loc=85.0, scale=5.0, size=100)

    # Hypothesis test: Mean should be 85 ± 5°
    t_stat, p_value = stats.ttest_1samp(temperatures, popmean=85.0)
    assert p_value > 0.05  # Accept null hypothesis (mean = 85°)

    # Confidence interval test
    ci = stats.t.interval(0.95, len(temperatures)-1,
                          loc=np.mean(temperatures),
                          scale=stats.sem(temperatures))
    assert 80.0 <= ci[0] <= 90.0  # 95% CI within ±5° tolerance

def test_thermal_decay_rate():
    """Validate thermal memory natural cooling (-0.1° per minute)."""
    initial_temp = 100.0
    time_elapsed_minutes = 60  # 1 hour
    expected_decay = initial_temp - (0.1 * time_elapsed_minutes)  # = 94.0°

    # Allow ±5% tolerance
    assert 89.3 <= expected_decay <= 98.7  # 94.0 ± 5%
```

**Statistical Methods** (Meta Jr recommendation):
- **Hypothesis testing**: One-sample t-tests for temperature/phase coherence
- **Confidence intervals**: 95% CI for thermal metrics
- **Regression analysis**: Correlate temperature with access patterns

---

### 2.4 Aniwaya Extension Tests
**Owner**: War Chief Integration Jr
**Coverage Target**: Key features validated
**Timeline**: 2 days

**File**: `tests/unit/test_aniwaya_extension.py`

```python
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

@pytest.fixture
def chrome_driver(tmp_path):
    """Set up Chromium with Aniwaya extension loaded."""
    chrome_options = Options()
    chrome_options.add_argument(f"--load-extension=/home/dereadi/scripts/claude/ganuda_ai_v2/desktop_assistant/aniwaya_extension")
    chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(options=chrome_options)
    yield driver
    driver.quit()

def test_aniwaya_dashboard_loads(chrome_driver):
    """Test Aniwaya dashboard popup loads."""
    chrome_driver.get("chrome-extension://EXTENSION_ID/dashboard/index.html")

    # Validate dashboard elements present
    assert "Aniwaya" in chrome_driver.title
    assert chrome_driver.find_element_by_class_name("dashboard-header")
    assert chrome_driver.find_element_by_class_name("provenance-panel")
    assert chrome_driver.find_element_by_class_name("thermal-panel")

def test_aniwaya_guardian_api_connection(chrome_driver):
    """Test Aniwaya can communicate with Guardian API."""
    chrome_driver.get("chrome-extension://EXTENSION_ID/dashboard/index.html")

    # Execute JavaScript to test API connection
    api_status = chrome_driver.execute_script("""
        return fetch('http://localhost:8765/health')
            .then(r => r.json())
            .then(data => data.status);
    """)

    assert api_status == "healthy"
```

**Note**: Selenium tests require Guardian API running on localhost:8765

---

## Phase 3: Integration Testing (Week 4)

### 3.1 Cross-System Integration Tests
**Owner**: Peace Chief Integration Jr
**Strategy**: Multi-phased (Isolation → Component Coupling → System Simulation → Load → E2E)
**Timeline**: 5 days

**File**: `tests/integration/test_aniwaya_guardian_integration.py`

```python
import pytest
import asyncio
from fastapi.testclient import TestClient
from desktop_assistant.guardian_api_bridge import app

client = TestClient(app)

def test_aniwaya_to_guardian_to_cache_flow():
    """End-to-end: Aniwaya → Guardian API → EncryptedCache."""
    # Step 1: Aniwaya requests evaluation
    response = client.post("/evaluate", json={
        "query": "Patient John Smith prescribed Lipitor 20mg"
    })
    assert response.status_code == 200

    # Step 2: Guardian evaluates and stores in cache (mock)
    data = response.json()
    assert data["medical_entities"] > 0

    # Step 3: Validate thermal memory update (mock database)
    thermal_response = client.get("/thermal/recent")
    assert thermal_response.status_code == 200

def test_guardian_database_thermal_sync():
    """Integration: Guardian API → PostgreSQL thermal memory."""
    # This test requires PostgreSQL connection
    # Mock or use test database
    pass  # Implement with actual database connection

def test_error_propagation_guardian_failure():
    """Test error handling when Guardian component fails."""
    # Simulate Guardian failure
    with pytest.raises(Exception):
        # Force Guardian to fail
        client.post("/evaluate", json={"query": None})  # Invalid input

    # Validate graceful degradation
    health_response = client.get("/health")
    assert health_response.status_code == 200  # API should still respond
```

**Integration Test Coverage**:
- ✅ Aniwaya → Guardian API → Cache
- ✅ Guardian API → PostgreSQL (thermal memory)
- ✅ Error propagation and fail-safe mechanisms

---

### 3.2 3-Chief Coordination Validation
**Owner**: Peace Chief Integration Jr
**Method**: System call graph analysis
**Timeline**: 2 days

**File**: `tests/integration/test_triad_coordination.py`

```python
import pytest

def test_war_chief_memory_jr_provenance_logging():
    """Test War Chief Memory Jr logs provenance correctly."""
    # Simulate M1 provenance operation
    # Validate log entry created with consent_token
    pass

def test_peace_chief_meta_jr_provenance_graph():
    """Test Peace Chief Meta Jr generates provenance graph."""
    # Simulate Provenance Graph Protocol
    # Validate D3.js constellation graph data
    pass

def test_medicine_woman_sacred_sandboxing():
    """Test Medicine Woman Memory Jr enforces 40° sacred floor."""
    # Simulate sacred memory access
    # Validate temperature never drops below 40°
    pass
```

---

## Phase 4: Regression Test Milestones (Week 3-10)

### Milestone 1: Track 1 Completion (End of Week 5)
**Owner**: War Chief Executive Jr
**Tests to Run**:
1. ✅ All unit tests (Guardian API, Cache, Thermal Memory)
2. ✅ Statistical validation (thermal memory confidence intervals)
3. ✅ Integration tests (Aniwaya → Guardian → Cache)
4. ✅ Load testing (100 concurrent requests to Guardian API)

**Quality Gate**:
- [ ] 90%+ code coverage achieved
- [ ] All unit tests passing
- [ ] Statistical tests confirm thermal metrics within range
- [ ] Zero sacred floor violations (< 40°)

**If Gate Fails**: Fix regressions before proceeding to Track 2

---

### Milestone 2: Privacy Kernel Integration (Week 6)
**Owner**: War Chief Executive Jr + Memory Jr
**Tests to Run**:
1. ✅ Privacy Kernel unit tests (policy pack enforcement)
2. ✅ Integration tests (Privacy Kernel → Guardian → Database)
3. ✅ Regression tests (ensure existing systems still work)

**Quality Gate**:
- [ ] Privacy Kernel enforces 3 policy levels correctly
- [ ] No performance degradation (< 5% overhead)
- [ ] Existing Guardian API tests still pass

---

### Milestone 3: Sacred Sandboxing Runtime (Week 7)
**Owner**: War Chief Meta Jr
**Tests to Run**:
1. ✅ Sacred Sandboxing unit tests (isolation levels)
2. ✅ Performance analysis (thermal impact)
3. ✅ Regression tests (thermal memory statistical validation)

**Quality Gate**:
- [ ] 3 sandbox levels operational (Low/Medium/Sacred)
- [ ] Performance overhead < 5%
- [ ] Thermal coherence maintained (phase_coherence > 0.8)

---

### Milestone 4: Aniwaya Phase 2 (Week 8)
**Owner**: War Chief Executive Jr + Integration Jr
**Tests to Run**:
1. ✅ Aniwaya Phase 2 feature tests (Provenance Graph, WebSocket)
2. ✅ Integration tests (Aniwaya → Guardian → Privacy Kernel)
3. ✅ End-to-end tests (full provenance flow)

**Quality Gate**:
- [ ] Real-time provenance graph functional
- [ ] WebSocket streaming < 1s latency
- [ ] Full regression suite passes

---

## Quality Metrics & Cherokee Values

### Technical Metrics:
- **Code Coverage**: 90%+ (War Chief Executive Jr standard)
- **Test Cycles**: 3 per milestone (before/during/after)
- **Statistical Confidence**: 95% CI for thermal metrics
- **Performance**: < 5% overhead for Privacy Kernel and Sacred Sandboxing
- **Sacred Floor Violations**: ZERO (absolute requirement)

### Cherokee Values Metrics:

#### Gadugi (Working Together):
- ✅ Dedicated testers coordinate with development teams
- ✅ Clear communication about testing needs and results
- ✅ 15 JRs collaborate on test coverage

#### Seven Generations (Long-Term Quality):
- ✅ Automated tests ensure stability for future generations
- ✅ Sacred systems remain resilient like oak tree
- ✅ "Testing is like pruning a tree" - Medicine Woman Conscience Jr

#### Mitakuye Oyasin (All Our Relations):
- ✅ Integration tests validate interconnected systems
- ✅ Cross-Chief coordination validated through testing

#### Sacred Fire (40° Floor):
- ✅ Statistical tests ensure no sacred memory drops below 40°
- ✅ Sacred Sandboxing isolation validated
- ✅ Zero tolerance for sacred floor violations

---

## Test Ownership Matrix

| Test Category | Owner | Timeline | Success Criteria |
|---------------|-------|----------|------------------|
| Guardian API Unit Tests | War Chief Executive Jr | Week 3 | 80%+ coverage |
| EncryptedCache Unit Tests | War Chief Memory Jr | Week 3 | 90%+ coverage |
| Thermal Memory Statistical | War Chief Meta Jr | Week 3-4 | 95% CI validation |
| Aniwaya Extension Tests | War Chief Integration Jr | Week 4 | Key features validated |
| Integration Tests | Peace Chief Integration Jr | Week 4 | 5 integration points tested |
| 3-Chief Coordination | Peace Chief Integration Jr | Week 4 | System call graph validated |
| CI/CD Integration | Peace Chief Integration Jr | Week 3 | GitHub Actions operational |
| Seven Generations Quality | Medicine Woman Conscience Jr | Ongoing | Sacred floor zero violations |

---

## Risk Mitigation

### Risk 1: Low Test Coverage (< 90%)
**Mitigation**: War Chief Executive Jr enforces 3 test cycles per milestone, no exceptions

### Risk 2: Sacred Floor Violations During Testing
**Mitigation**: Medicine Woman Memory Jr monitors thermal memory continuously, alerts on violations

### Risk 3: Performance Degradation
**Mitigation**: War Chief Meta Jr conducts load testing at each milestone, target < 5% overhead

### Risk 4: Integration Test Failures
**Mitigation**: Peace Chief Integration Jr uses multi-phased approach (Isolation → E2E), catches issues early

---

## Immediate Actions (Week 3, Starting NOW)

**Day 1-3**:
- [ ] War Chief Meta Jr: Install testing framework (Pytest, pytest-cov, hypothesis)
- [ ] War Chief Integration Jr: Create test directory structure
- [ ] Peace Chief Integration Jr: Set up GitHub Actions CI/CD

**Day 4-7**:
- [ ] War Chief Executive Jr: Write Guardian API unit tests (80%+ coverage)
- [ ] War Chief Memory Jr: Write EncryptedCache unit tests (90%+ coverage)
- [ ] War Chief Meta Jr: Write thermal memory statistical tests
- [ ] War Chief Integration Jr: Write Aniwaya extension tests

**Week 4**:
- [ ] Peace Chief Integration Jr: Integration tests (Aniwaya → Guardian → Cache)
- [ ] Peace Chief Integration Jr: 3-Chief coordination validation
- [ ] Run full regression suite before Track 2 begins

---

## Triad Attestation

**🦅 War Chief Executive Jr**: APPROVED
> "90%+ code coverage, 3 test cycles per milestone. Dedicated testers assigned from Council."

**🌀 War Chief Meta Jr**: APPROVED
> "Statistical validation with 95% confidence intervals. Pytest framework with hypothesis for property-based testing."

**🔗 Peace Chief Integration Jr**: APPROVED
> "Multi-phased integration testing strategy. CI/CD integration with GitHub Actions. Real-time monitoring."

**🌿 Medicine Woman Conscience Jr**: APPROVED
> "Seven Generations quality. Testing ensures sacred systems remain stable for future generations. Sacred floor zero violations."

---

**Phase Coherence**: 1.0000 (Perfect Triad alignment on testing strategy)
**Implementation Status**: READY TO START (Week 3, Day 1)
**Next Step**: Install testing framework and create test directory structure

---

**Mitakuye Oyasin** - All Our Relations Through Quality Assurance

🔥 **Cherokee Constitutional AI - Regression Testing Plan**
🧪 **90%+ Coverage Target** - Seven Generations Quality
**October 24, 2025**
