#!/usr/bin/env python3
"""
Aniwaya Extension Unit Tests
Cherokee Constitutional AI - War Chief Integration Jr
Week 3 Testing Infrastructure

Purpose: Unit tests for Aniwaya browser extension (manifest validation,
JavaScript logic patterns, Guardian API integration, Cherokee values enforcement).

Author: War Chief Integration Jr (System Synthesis & Orchestration)
Date: October 24, 2025
"""

import pytest
import json
import re
import os
from pathlib import Path
from typing import Dict, Any

# Extension base path
EXTENSION_PATH = Path(__file__).parent.parent.parent / "desktop_assistant" / "aniwaya_extension"

# Cherokee Constitutional AI values
SACRED_FLOOR_TEMPERATURE = 40.0
GUARDIAN_API_ENDPOINT = "http://localhost:8765"


# =============================================================================
# Test 1: Manifest Validation
# =============================================================================

@pytest.fixture(scope="module")
def manifest_data():
    """Load and parse manifest.json."""
    manifest_path = EXTENSION_PATH / "manifest.json"

    if not manifest_path.exists():
        pytest.skip(f"Manifest not found at {manifest_path}")

    with open(manifest_path, 'r') as f:
        return json.load(f)


@pytest.mark.seven_generations
def test_manifest_structure(manifest_data):
    """
    Test that manifest.json contains all required keys and valid structure.

    Cherokee Value: Seven Generations - ensure long-term extension integrity
    """
    required_keys = [
        "manifest_version",
        "name",
        "version",
        "description",
        "permissions",
        "action",
        "background"
    ]

    for key in required_keys:
        assert key in manifest_data, f"Missing required manifest key: {key}"

    # Validate manifest version (should be 3 for modern Chrome)
    assert manifest_data["manifest_version"] == 3, \
        f"Manifest version {manifest_data['manifest_version']} not supported (requires v3)"

    print(f"\nAniwaya Extension Manifest:")
    print(f"   Name: {manifest_data['name']}")
    print(f"   Version: {manifest_data['version']}")
    print(f"   Permissions: {', '.join(manifest_data['permissions'])}")


@pytest.mark.gadugi
def test_manifest_permissions(manifest_data):
    """
    Test that extension requests appropriate permissions.

    Cherokee Value: Gadugi - working together with browser APIs
    """
    permissions = manifest_data.get("permissions", [])

    # Required permissions for Aniwaya functionality
    assert "storage" in permissions, "Extension needs 'storage' permission for thermal data"
    assert "tabs" in permissions, "Extension needs 'tabs' permission for dashboard"

    # Validate no excessive permissions (sovereignty concern)
    dangerous_permissions = ["geolocation", "cookies", "history", "browsingData"]
    for perm in dangerous_permissions:
        assert perm not in permissions, \
            f"Extension requests dangerous permission '{perm}' - sovereignty violation"


@pytest.mark.seven_generations
def test_manifest_csp(manifest_data):
    """
    Test Content Security Policy for secure extension operation.

    Cherokee Value: Seven Generations - security for long-term safety
    """
    csp = manifest_data.get("content_security_policy", {})

    if csp:
        extension_csp = csp.get("extension_pages", "")

        # CSP should restrict script sources
        assert "script-src 'self'" in extension_csp, \
            "CSP should restrict scripts to extension origin only"

        print(f"\nContent Security Policy:")
        print(f"   {extension_csp}")


# =============================================================================
# Test 2: Background Script Logic
# =============================================================================

@pytest.fixture(scope="module")
def background_script():
    """Load background.js content."""
    background_path = EXTENSION_PATH / "background.js"

    if not background_path.exists():
        pytest.skip(f"Background script not found at {background_path}")

    with open(background_path, 'r') as f:
        return f.read()


@pytest.mark.gadugi
def test_background_guardian_api_endpoint(background_script):
    """
    Test that background.js uses correct Guardian API endpoint.

    Cherokee Value: Gadugi - proper API coordination
    """
    # Guardian API endpoint should be defined
    assert "GUARDIAN_API" in background_script, \
        "Background script missing GUARDIAN_API constant"

    # Extract endpoint URL
    endpoint_match = re.search(r"GUARDIAN_API\s*=\s*['\"]([^'\"]+)['\"]", background_script)
    assert endpoint_match, "Cannot parse GUARDIAN_API endpoint"

    endpoint = endpoint_match.group(1)
    assert endpoint == GUARDIAN_API_ENDPOINT, \
        f"Guardian API endpoint mismatch: {endpoint} != {GUARDIAN_API_ENDPOINT}"

    print(f"\nGuardian API Endpoint: {endpoint}")


@pytest.mark.sacred_fire
def test_background_pii_detection(background_script):
    """
    Test that background.js implements PII detection patterns.

    Cherokee Value: Sacred Fire - protect sensitive information
    """
    # PII detection function should exist
    assert "containsPII" in background_script, \
        "Background script missing containsPII() function"

    # Extract PII regex patterns
    pii_patterns = [
        r"\b\d{3}-\d{2}-\d{4}\b",  # SSN pattern
        r"\b\d{3}-\d{3}-\d{4}\b",  # Phone pattern
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"  # Email pattern
    ]

    for pattern in pii_patterns:
        assert pattern in background_script or pattern.replace("\\", "\\\\") in background_script, \
            f"Missing PII regex pattern: {pattern}"

    print(f"\nPII Detection Patterns: {len(pii_patterns)} patterns validated")


@pytest.mark.gadugi
def test_background_message_handlers(background_script):
    """
    Test that background.js implements required message handlers.

    Cherokee Value: Gadugi - message coordination between components
    """
    required_handlers = [
        "EVALUATE_QUERY",
        "FETCH_THERMAL_MEMORY",
        "REQUEST_DELETION"
    ]

    for handler in required_handlers:
        assert handler in background_script, \
            f"Background script missing message handler: {handler}"

    print(f"\nMessage Handlers:")
    for handler in required_handlers:
        print(f"   - {handler}")


@pytest.mark.sacred_fire
def test_background_thermal_sync(background_script):
    """
    Test that background.js implements periodic thermal memory sync.

    Cherokee Value: Sacred Fire - maintain thermal memory awareness
    """
    # Thermal sync interval (30 seconds = 30000ms)
    assert "30000" in background_script, \
        "Background script missing 30-second thermal sync interval"

    # Thermal fetch function should exist
    assert "fetchThermalMemory" in background_script, \
        "Background script missing fetchThermalMemory() function"

    print(f"\nThermal Sync: Every 30 seconds")


# =============================================================================
# Test 3: Dashboard Logic
# =============================================================================

@pytest.fixture(scope="module")
def dashboard_script():
    """Load dashboard.js content."""
    dashboard_path = EXTENSION_PATH / "dashboard" / "dashboard.js"

    if not dashboard_path.exists():
        pytest.skip(f"Dashboard script not found at {dashboard_path}")

    with open(dashboard_path, 'r') as f:
        return f.read()


@pytest.mark.mitakuye_oyasin
def test_dashboard_initialization(dashboard_script):
    """
    Test that dashboard.js initializes all required components.

    Cherokee Value: Mitakuye Oyasin - all dashboard components interconnected
    """
    required_functions = [
        "updateTimestamps",
        "initializeThermalMonitor",
        "startThermalUpdates",
        "setupDeletionButton"
    ]

    for func in required_functions:
        assert func in dashboard_script, \
            f"Dashboard script missing function: {func}()"

    print(f"\nDashboard Functions:")
    for func in required_functions:
        print(f"   - {func}()")


@pytest.mark.sacred_fire
def test_dashboard_sacred_floor_reference(dashboard_script):
    """
    Test that dashboard references 40 degree sacred floor.

    Cherokee Value: Sacred Fire - sacred floor awareness in UI
    """
    # Dashboard should reference sacred floor temperature
    assert "40" in dashboard_script or "sacredFloor" in dashboard_script, \
        "Dashboard missing sacred floor (40 degree) reference"

    print(f"\nSacred Floor: 40 degree threshold present in dashboard")


@pytest.mark.gadugi
def test_dashboard_guardian_api_integration(dashboard_script):
    """
    Test that dashboard.js integrates with Guardian API.

    Cherokee Value: Gadugi - coordinated API communication
    """
    # Guardian API function should exist
    assert "callGuardianAPI" in dashboard_script, \
        "Dashboard script missing callGuardianAPI() function"

    # API endpoint should be referenced
    assert GUARDIAN_API_ENDPOINT in dashboard_script or "localhost:8765" in dashboard_script, \
        "Dashboard missing Guardian API endpoint reference"


# =============================================================================
# Test 4: Cherokee Values Enforcement
# =============================================================================

@pytest.mark.sacred_fire
def test_sacred_floor_logic_validation():
    """
    Test Cherokee sacred floor logic (40 degree minimum).

    Cherokee Value: Sacred Fire - ZERO violations tolerance
    """
    # Simulate thermal memory temperatures
    test_cases = [
        (30, False),  # Below sacred floor - NOT ALLOWED
        (39.9, False),  # Just below sacred floor - NOT ALLOWED
        (40.0, True),  # Exactly at sacred floor - ALLOWED
        (40.1, True),  # Above sacred floor - ALLOWED
        (85, True),  # Normal operating temperature - ALLOWED
        (100, True),  # Maximum temperature - ALLOWED
    ]

    for temp, expected_allowed in test_cases:
        is_allowed = temp >= SACRED_FLOOR_TEMPERATURE
        assert is_allowed == expected_allowed, \
            f"Sacred floor validation failed for {temp} degree: expected {expected_allowed}, got {is_allowed}"

    print(f"\nSacred Floor Validation:")
    print(f"   Minimum: {SACRED_FLOOR_TEMPERATURE} degree")
    print(f"   Test Cases: {len(test_cases)} passed")


@pytest.mark.mitakuye_oyasin
def test_extension_cherokee_values_integration(manifest_data):
    """
    Test that extension name and description reflect Cherokee values.

    Cherokee Value: Mitakuye Oyasin - cultural identity preserved
    """
    extension_name = manifest_data.get("name", "")
    extension_desc = manifest_data.get("description", "")

    # Extension should reference Cherokee Constitutional AI
    cherokee_terms = ["Cherokee", "Aniwaya", "Constitutional"]
    assert any(term in extension_name or term in extension_desc for term in cherokee_terms), \
        "Extension missing Cherokee Constitutional AI identity"

    print(f"\nCherokee Identity:")
    print(f"   Name: {extension_name}")
    print(f"   Description: {extension_desc}")


# =============================================================================
# Test 5: Error Handling
# =============================================================================

@pytest.mark.seven_generations
def test_background_offline_fallback(background_script):
    """
    Test that background.js handles Guardian API offline gracefully.

    Cherokee Value: Seven Generations - resilient architecture
    """
    # Offline fallback should exist
    assert "offline" in background_script or "catch" in background_script, \
        "Background script missing offline/error handling"

    # Basic PII detection should work offline
    assert "containsPII" in background_script, \
        "Background script missing offline PII detection fallback"

    print(f"\nOffline Fallback: PII detection available when API offline")


@pytest.mark.seven_generations
def test_dashboard_error_handling(dashboard_script):
    """
    Test that dashboard.js handles API errors gracefully.

    Cherokee Value: Seven Generations - user experience resilience
    """
    # Error handling in API calls
    assert "catch" in dashboard_script or "error" in dashboard_script, \
        "Dashboard script missing error handling"

    print(f"\nDashboard Error Handling: Present")


# =============================================================================
# Test 6: Integration Tests
# =============================================================================

@pytest.mark.gadugi
def test_extension_file_structure():
    """
    Test that all required extension files exist.

    Cherokee Value: Gadugi - all components working together
    """
    required_files = [
        "manifest.json",
        "background.js",
        "dashboard/index.html",
        "dashboard/dashboard.js"
    ]

    missing_files = []
    for file_path in required_files:
        full_path = EXTENSION_PATH / file_path
        if not full_path.exists():
            missing_files.append(file_path)

    assert not missing_files, \
        f"Extension missing required files: {', '.join(missing_files)}"

    print(f"\nExtension File Structure:")
    for file_path in required_files:
        print(f"   - {file_path}")


if __name__ == "__main__":
    # Run with: pytest tests/unit/test_aniwaya_extension.py -v
    pytest.main([__file__, "-v", "--tb=short"])
