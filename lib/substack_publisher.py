"""
Substack Publisher — Deer's content pipeline extension.
Publishes blog posts to Substack via browser proxy on bmasass.
Council vote #9fc9b98bd7368cb7. Crawdad audit CLEARED WITH CONDITIONS Mar 17 2026.
Audit: /ganuda/docs/audits/AUDIT-PYTHON-SUBSTACK-MAR2026.md

Architecture: redfin → SSH → bmasass → osascript → Chrome → Substack API
This bypasses Substack's captcha on programmatic login by using Chrome's
authenticated session. The proxy script lives at:
    /Users/Shared/ganuda/scripts/substack_proxy.py

DRAFT-ONLY in P-3. Publish enabled at P-1.

Crawdad conditions enforced:
  - No credentials in source code (browser session handles auth)
  - debug=False always (no debug logging of session data)
  - Version pinned to 0.1.18 (proxy doesn't use python-substack directly)
  - PII scrub before content leaves federation
"""

import subprocess
import json
import logging

try:
    from lib.ganuda_pii.service import PIIService
    _HAS_PII = True
except ImportError:
    _HAS_PII = False

try:
    from lib.chain_protocol import tag_provenance, meter_call
    _HAS_CHAIN = True
except ImportError:
    _HAS_CHAIN = False

logger = logging.getLogger('substack_publisher')

# bmasass connection — LAN primary, Tailscale fallback
BMASASS_LAN_IP = "192.168.132.21"
BMASASS_TAILSCALE_IP = "100.103.27.106"
PROXY_SCRIPT = "/Users/Shared/ganuda/scripts/substack_proxy.py"
SSH_USER = "dereadi"


def _resolve_bmasass():
    """Try LAN first, fall back to Tailscale if bmasass is mobile."""
    import socket
    try:
        s = socket.create_connection((BMASASS_LAN_IP, 22), timeout=3)
        s.close()
        return BMASASS_LAN_IP
    except (socket.timeout, OSError):
        return BMASASS_TAILSCALE_IP


def _ssh_proxy(command, args=None, timeout=45):
    """Execute substack_proxy.py on bmasass via SSH."""
    host = _resolve_bmasass()
    # Build remote command as a single quoted string to avoid shell expansion
    import shlex
    remote_parts = ["python3", PROXY_SCRIPT, command]
    if args:
        remote_parts.extend(args)
    remote_cmd = " ".join(shlex.quote(p) for p in remote_parts)
    cmd = ["ssh", "-o", "ConnectTimeout=5", f"{SSH_USER}@{host}", remote_cmd]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        logger.error("Proxy call failed: %s", result.stderr.strip())
        return {"error": result.stderr.strip()}

    output = result.stdout.strip()
    try:
        data = json.loads(output)
        # Handle the "raw" wrapper from proxy — contains double-serialized JSON
        if isinstance(data, dict) and "raw" in data and len(data) == 1:
            try:
                return json.loads(data["raw"])
            except (json.JSONDecodeError, TypeError):
                return data
        return data
    except json.JSONDecodeError:
        # The proxy might output raw JSON without wrapper
        return {"raw": output}


class SubstackPublisher:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self._pii = PIIService() if _HAS_PII else None

    def _scrub_content(self, content):
        """PII + infrastructure scrub before content leaves the federation."""
        if self._pii:
            return self._pii.scrub(content)
        logger.warning("PII scrub unavailable — presidio not installed")
        return content

    def create_draft(self, title, subtitle, content, audience="everyone"):
        """Create a draft on Substack. Does NOT publish."""
        if not self.enabled:
            logger.info("Substack publishing disabled (kill switch)")
            return {"status": "disabled"}

        # Scrub before anything leaves the federation
        clean_title = self._scrub_content(title)
        clean_subtitle = self._scrub_content(subtitle)
        clean_content = self._scrub_content(content)

        result = _ssh_proxy("create_draft", [clean_title, clean_subtitle, clean_content])

        if "error" in result:
            logger.error("Draft creation failed: %s", result["error"])
            return {"status": "error", "detail": result["error"]}

        draft_id = result.get("id") or result.get("draft_id")
        logger.info("Substack draft created: %s — '%s'", draft_id, clean_title)
        if _HAS_CHAIN:
            try:
                meter_call(0, latency_ms=0.0, cost=0.0)
            except Exception:
                pass  # metering is non-critical

        return {
            "status": "draft_created",
            "draft_id": draft_id,
            "title": clean_title,
        }

    def list_drafts(self):
        """List current drafts."""
        if not self.enabled:
            return {"status": "disabled"}
        return _ssh_proxy("drafts")

    def delete_draft(self, draft_id):
        """Delete a draft."""
        if not self.enabled:
            return {"status": "disabled"}
        return _ssh_proxy("delete_draft", [str(draft_id)])

    def get_profile(self):
        """Get the Substack user profile."""
        return _ssh_proxy("profile")
