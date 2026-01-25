"""
ganuda-council: 7-Specialist Council Integration
Cherokee AI Federation - For the Seven Generations

CORE PACKAGE - Shared across all Assist applications

Features:
- Council vote client (redfin:8080)
- Consensus extraction
- Specialist attribution
- Vote history tracking

Usage:
    from ganuda_council import CouncilClient, council_vote

    client = CouncilClient()
    result = client.vote("What is the best approach?", context="...")

Note: Domain-specific prompts stay in the app.
This package provides the generic Council interface.
"""

__version__ = "1.0.0"

# The existing specialist_council.py in /ganuda/lib/ is the implementation
# This package provides a cleaner interface

import sys
import importlib.util

# Load existing council implementation
_council_path = "/ganuda/lib/specialist_council.py"
_spec = importlib.util.spec_from_file_location("specialist_council", _council_path)
_council_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_council_module)

# Export key components
SpecialistCouncil = _council_module.SpecialistCouncil
council_vote = _council_module.council_vote

__all__ = ["SpecialistCouncil", "council_vote"]
