# JR Instruction: VetAssist Research Regression Tests

**JR ID:** JR-VETASSIST-RESEARCH-REGRESSION-TESTS-JAN28-2026
**Priority:** P2
**Assigned To:** QA Jr.
**Related:** KB-VETASSIST-II-RESEARCHER-INTEGRATION-JAN28-2026

---

## Objective

Add regression tests for VetAssist research integration to prevent future breakage.

---

## Tests Needed

### File: `/ganuda/vetassist/backend/tests/test_research.py`

```python
"""
Tests for VetAssist research integration with ii-researcher.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Test fixtures
@pytest.fixture
def research_request():
    return {
        "veteran_id": "test-vet-001",
        "session_id": "test-session",
        "question": "What is the VA rating for tinnitus?",
        "condition": "tinnitus",
        "max_steps": 3
    }

# Test /trigger endpoint
class TestResearchTrigger:
    def test_trigger_creates_request_file(self, client, research_request):
        """POST /research/trigger should create request file"""
        response = client.post("/api/v1/research/trigger", json=research_request)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "research_queued"
        assert "request_id" in data

    def test_trigger_requires_question(self, client):
        """POST /research/trigger should fail without question"""
        response = client.post("/api/v1/research/trigger", json={
            "session_id": "test",
            "veteran_id": "test"
        })
        assert response.status_code == 422  # Validation error

# Test /results endpoint
class TestResearchResults:
    def test_results_empty_for_new_veteran(self, client):
        """GET /research/results should return empty for new veteran"""
        response = client.get("/api/v1/research/results/nonexistent-veteran")
        assert response.status_code == 200
        data = response.json()
        assert data["research_count"] == 0
        assert data["results"] == []

    def test_results_returns_completed_research(self, client, db_session):
        """GET /research/results should return completed research"""
        # Insert test data
        db_session.execute("""
            INSERT INTO vetassist_research_results
            (veteran_id, job_id, question, answer, sources)
            VALUES ('test-vet', 'job-123', 'Test question?', 'Test answer', '[]')
        """)
        db_session.commit()

        response = client.get("/api/v1/research/results/test-vet")
        assert response.status_code == 200
        data = response.json()
        assert data["research_count"] == 1
        assert data["results"][0]["question"] == "Test question?"

# Test dashboard research_history
class TestDashboardResearchHistory:
    def test_dashboard_includes_research_history(self, client, db_session):
        """Dashboard should include research_history array"""
        response = client.get("/api/v1/dashboard/test-veteran")
        assert response.status_code == 200
        data = response.json()
        assert "research_history" in data
        assert isinstance(data["research_history"], list)
```

---

## Pre-existing Test Failures

The following tests were failing before research integration (unrelated):

- `test_auth_endpoints.py` - Auth flow tests (15 failures)
- `test_security.py` - Password/JWT tests

**Recommendation:** Create separate JR to fix auth test fixtures.

---

## Validation

```bash
cd /ganuda/vetassist/backend
source venv/bin/activate
python -m pytest tests/test_research.py -v
```

---

FOR SEVEN GENERATIONS
