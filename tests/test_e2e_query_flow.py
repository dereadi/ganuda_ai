"""
Cherokee Constitutional AI - End-to-End Tests
Testing: Complete query flow from CLI to thermal memory

Phase 2B - E2E testing layer
"""

import pytest
import subprocess
import time


class TestEndToEndQueryFlow:
    """
    End-to-end tests for complete query cycle:
    1. User sends CLI query
    2. Chiefs deliberate
    3. Response returned
    4. Thermal memory updated
    
    NOTE: These tests require the tribe to be running
    (PostgreSQL + Jr daemons). Run 'make up' first.
    """
    
    @pytest.mark.e2e
    @pytest.mark.skip(reason="Requires running tribe infrastructure")
    def test_complete_query_cycle(self):
        """
        Test complete query flow:
        - Send query via query_triad.py
        - Receive response in <2 seconds
        - Verify thermal memory updated
        """
        start_time = time.time()
        
        # Execute query
        result = subprocess.run(
            ["python3", "scripts/query_triad.py", "What is your purpose?"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Verify response received
        assert result.returncode == 0
        assert "ANSWER" in result.stdout
        
        # Verify response time < 2 seconds
        assert response_time < 2.0, f"Response took {response_time}s, expected <2s"
        
        # TODO: Verify thermal memory was updated
        # Would query database to confirm memory_id was created
    
    @pytest.mark.e2e
    @pytest.mark.skip(reason="Requires running tribe infrastructure")
    def test_tribal_deliberation_cycle(self):
        """
        Test complete deliberation flow:
        - Run tribal_deliberation_vote.py
        - Receive all Jr votes
        - Verify consensus reached
        """
        result = subprocess.run(
            ["python3", "scripts/tribal_deliberation_vote.py"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Verify deliberation completed
        assert result.returncode == 0
        assert "TRIBAL CONSENSUS" in result.stdout
        assert "VOTE:" in result.stdout
        
        # Verify all Jrs voted
        assert "Memory Jr" in result.stdout
        assert "Executive Jr" in result.stdout
        assert "Meta Jr" in result.stdout


class TestAPIEndpoints:
    """
    End-to-end tests for FastAPI endpoints
    
    NOTE: Requires API server running on port 8000
    """
    
    @pytest.mark.e2e
    @pytest.mark.skip(reason="Requires running API server")
    def test_api_health_endpoint(self):
        """Test /health endpoint returns healthy status"""
        import requests
        
        response = requests.get("http://localhost:8000/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @pytest.mark.e2e
    @pytest.mark.skip(reason="Requires running API server")
    def test_api_thermal_endpoint(self):
        """Test /thermal endpoint returns memory status"""
        import requests
        
        response = requests.get("http://localhost:8000/thermal")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_memories" in data
        assert "average_temperature" in data
        assert data["average_temperature"] >= 0
        assert data["average_temperature"] <= 100


class TestDockerHealthChecks:
    """
    End-to-end tests for Docker health checks
    
    NOTE: Requires Docker infrastructure running
    """
    
    @pytest.mark.e2e
    @pytest.mark.skip(reason="Requires Docker infrastructure")
    def test_all_containers_healthy(self):
        """Verify all containers pass health checks"""
        result = subprocess.run(
            ["docker-compose", "-f", "infra/docker-compose.yml", "ps"],
            capture_output=True,
            text=True
        )
        
        # All containers should show as "healthy"
        assert "healthy" in result.stdout
        assert "unhealthy" not in result.stdout
    
    @pytest.mark.e2e
    @pytest.mark.skip(reason="Requires Docker infrastructure")
    def test_postgres_connectivity(self):
        """Test PostgreSQL is accessible from containers"""
        result = subprocess.run(
            [
                "docker-compose", "-f", "infra/docker-compose.yml",
                "exec", "-T", "postgres",
                "psql", "-U", "cherokee", "-d", "cherokee_ai", "-c", "SELECT 1;"
            ],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not e2e"])
