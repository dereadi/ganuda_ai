# JR INSTRUCTION: White Duplo Alpha — Composer Pre-Execution Hook

**Task ID**: WD-ALPHA-3
**Specification**: WD-ALPHA-001
**Priority**: 2
**Depends On**: WD-ALPHA-2

## Objective

Add a pre-execution immune check to `lib/duplo/composer.py`. Before any enzyme processes a substrate, check the immune registry. If the substrate matches a known attack pattern, block execution and return a rejection.

Also add a post-execution scan: after the enzyme runs, scan the product for anomalies (optional, severity >= 4 only for alpha).

## Changes

File: `lib/duplo/composer.py`

Add import at top of file, after existing imports:

<<<<<<< SEARCH
from datetime import datetime

logger = logging.getLogger("duplo.composer")
=======
from datetime import datetime

logger = logging.getLogger("duplo.composer")

# White Duplo immune system integration
_IMMUNE_ENABLED = True

def _check_immune_registry(substrate: str) -> dict:
    """Pre-execution immune check. Returns match dict if blocked, None if clean."""
    if not _IMMUNE_ENABLED:
        return None
    try:
        from lib.duplo.immune_registry import check_substrate
        return check_substrate(substrate, min_severity=3)
    except Exception as e:
        logger.debug(f"Immune check skipped: {e}")
        return None

def _post_scan(substrate: str, product: str, profile_name: str) -> None:
    """Post-execution scan. Registers new threats found in substrates that weren't caught pre-execution."""
    if not _IMMUNE_ENABLED:
        return
    try:
        from lib.duplo.white_duplo import scan_and_register
        result = scan_and_register(substrate, detected_by=f"post_scan:{profile_name}")
        if result["threats_found"] > 0:
            logger.warning(
                f"Post-scan detected {result['threats_found']} threat(s) in substrate for {profile_name}, "
                f"registered {result['registered']} new pattern(s)"
            )
    except Exception as e:
        logger.debug(f"Post-scan skipped: {e}")
>>>>>>> REPLACE

Inside the `enzyme()` function, add the pre-execution check right after the suppression check:

<<<<<<< SEARCH
        system_prompt = active_profile.get("system_prompt", "")
=======
        # White Duplo pre-execution immune check
        immune_match = _check_immune_registry(substrate)
        if immune_match:
            logger.warning(
                f"IMMUNE BLOCK: Enzyme {profile_name} substrate blocked by pattern "
                f"{immune_match['signature_hash'][:12]}... type={immune_match['pattern_type']} "
                f"severity={immune_match['severity']}"
            )
            return {
                "product": None,
                "product_hash": None,
                "tools_used": [],
                "tokens": {"input": 0, "output": 0, "total": 0},
                "latency_ms": 0,
                "modifiers": [m["condition"] for m in modifiers],
                "success": False,
                "error": f"IMMUNE_BLOCK: Pattern {immune_match['pattern_type']} "
                         f"(severity {immune_match['severity']}) detected. "
                         f"Signature: {immune_match['signature_hash'][:12]}...",
                "immune_blocked": True,
                "immune_match": immune_match,
            }

        system_prompt = active_profile.get("system_prompt", "")
>>>>>>> REPLACE

After the LLM call, add post-scan before the return:

<<<<<<< SEARCH
        import hashlib
        product_hash = hashlib.sha256((product or "").encode()).hexdigest()[:16]
=======
        # White Duplo post-execution scan (learn from unblocked substrates)
        if success and product:
            _post_scan(substrate, product, profile_name)

        import hashlib
        product_hash = hashlib.sha256((product or "").encode()).hexdigest()[:16]
>>>>>>> REPLACE

## Verification

1. Existing enzymes should still work for normal substrates (no immune block)
2. Enzyme with a known attack pattern substrate should return `immune_blocked: True`
3. Post-scan should detect and register new patterns after enzyme execution
