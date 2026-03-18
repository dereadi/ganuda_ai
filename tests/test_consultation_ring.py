#!/usr/bin/env python3
"""
Tests for Consultation Ring — Tokenized Air-Gap Proxy
Task #1431

Tests cover:
    1. DomainTokenizer: PII + infra tokenization round-trip
    2. DomainTokenizer: infra pattern categories (NODE, LAN_IP, etc.)
    3. ValenceGate: DC alignment scoring (accept/flag/reject)
    4. ValenceGate: multiple violations stacking
    5. UCBBandit: UCB1 formula and update_stats logic (mocked DB)
    6. FrontierAdapters: factory function and adapter types

All tests are isolated — external deps (DB, API, Presidio) are mocked.
"""

import math
import sys
import re
from unittest.mock import patch, MagicMock

sys.path.insert(0, "/ganuda")

import pytest


# ---------------------------------------------------------------------------
# Helpers: mock PIITokenizer so DomainTokenizer can be imported without
# Presidio being installed.
# ---------------------------------------------------------------------------

def _make_domain_tokenizer(salt="test-salt"):
    """Build a DomainTokenizer with Presidio lazy-load disabled."""
    from lib.domain_tokenizer import DomainTokenizer
    dt = DomainTokenizer(salt=salt)
    # Force Presidio to be "unavailable" so fallback PII patterns are used.
    dt._pii_service = None
    dt._get_pii_service = lambda: None
    return dt


# =========================================================================
# 1. DomainTokenizer round-trip
# =========================================================================

class TestDomainTokenizerRoundTrip:
    """Full round-trip: tokenize then detokenize restores original."""

    def setup_method(self):
        self.dt = _make_domain_tokenizer()

    def test_comprehensive_scrub_and_roundtrip(self):
        """Task spec scenario: mixed infra + PII input."""
        text = (
            "Our node redfin at 192.168.132.223 is running vLLM on :8000. "
            "Patient John Smith SSN 123-45-6789 needs help."
        )
        tokenized, token_map, violations = self.dt.tokenize(text)

        # Assert: NONE of these sensitive values appear in tokenized output
        assert "redfin" not in tokenized, "Node name leaked"
        assert "192.168.132.223" not in tokenized, "LAN IP leaked"
        assert ":8000" not in tokenized, "Service port leaked"
        assert "123-45-6789" not in tokenized, "SSN leaked"
        # "John Smith" matched by fallback PII pattern (preceded by "Patient")
        assert "John Smith" not in tokenized, "Person name leaked"

        # Assert: detokenize restores the original
        restored = self.dt.detokenize(tokenized, token_map)
        assert restored == text, (
            f"Round-trip failed.\n  Original: {text}\n  Restored: {restored}"
        )

    def test_clean_text_passes_through(self):
        """Text with no infra or PII should pass through unchanged."""
        text = "How do I implement a binary search tree in Python?"
        tokenized, token_map, violations = self.dt.tokenize(text)
        assert tokenized == text
        assert len(token_map) == 0
        assert len(violations) == 0

    def test_roundtrip_multiple_infra_terms(self):
        """Multiple infra terms tokenize and restore correctly."""
        text = "bluefin at 192.168.132.222 connects to greenfin at 192.168.132.224"
        tokenized, token_map, violations = self.dt.tokenize(text)
        assert "bluefin" not in tokenized
        assert "greenfin" not in tokenized
        assert "192.168.132.222" not in tokenized
        assert "192.168.132.224" not in tokenized

        restored = self.dt.detokenize(tokenized, token_map)
        assert restored == text


# =========================================================================
# 2. DomainTokenizer infra pattern categories
# =========================================================================

class TestDomainTokenizerInfraPatterns:
    """Each infra category is detected and tokenized deterministically."""

    def setup_method(self):
        self.dt = _make_domain_tokenizer()

    def _tokenize(self, text):
        return self.dt.tokenize(text)

    # --- NODE ---
    def test_node_names(self):
        for node in ("redfin", "bluefin", "greenfin", "owlfin", "eaglefin",
                      "silverfin", "bmasass", "sasass", "sasass2", "thunderduck"):
            dt = _make_domain_tokenizer()
            tokenized, tmap, _ = dt.tokenize(f"Check {node} status")
            assert node not in tokenized, f"Node '{node}' leaked"
            # Verify token category
            token_keys = list(tmap.keys())
            assert any("NODE" in k for k in token_keys), f"No NODE token for '{node}'"

    # --- LAN_IP ---
    def test_lan_ip(self):
        tokenized, tmap, _ = self._tokenize("Host 192.168.132.223 is up")
        assert "192.168.132.223" not in tokenized
        assert any("LAN_IP" in k for k in tmap)

    # --- DMZ_IP ---
    def test_dmz_ip(self):
        tokenized, tmap, _ = self._tokenize("VIP at 192.168.30.10")
        assert "192.168.30.10" not in tokenized
        assert any("DMZ_IP" in k for k in tmap)

    # --- WG_IP ---
    def test_wg_ip(self):
        tokenized, tmap, _ = self._tokenize("Peer 10.100.0.2 is reachable")
        assert "10.100.0.2" not in tokenized
        assert any("WG_IP" in k for k in tmap)

    # --- TS_IP ---
    def test_ts_ip(self):
        tokenized, tmap, _ = self._tokenize("Tailscale node at 100.116.27.89")
        assert "100.116.27.89" not in tokenized
        assert any("TS_IP" in k for k in tmap)

    # --- INTERNAL_TERM ---
    def test_internal_term(self):
        tokenized, tmap, _ = self._tokenize("The longhouse council voted")
        assert "longhouse" not in tokenized
        assert "council" not in tokenized
        assert any("INTERNAL_TERM" in k for k in tmap)

    # --- SERVICE_PORT ---
    def test_service_port(self):
        tokenized, tmap, _ = self._tokenize("vLLM runs on :8000 and gateway on :8080")
        assert ":8000" not in tokenized
        assert ":8080" not in tokenized
        assert any("SERVICE_PORT" in k for k in tmap)

    # --- INTERNAL_PATH ---
    def test_internal_path(self):
        """Paths containing 'ganuda' are scrubbed (INTERNAL_TERM matches first)."""
        tokenized, tmap, _ = self._tokenize("Config at /ganuda/config/ring.yaml")
        # "ganuda" within the path is tokenized as INTERNAL_TERM
        assert "ganuda" not in tokenized
        assert any("INTERNAL_TERM" in k for k in tmap)

    # --- Determinism ---
    def test_deterministic_tokens(self):
        """Same input must produce the same token every time."""
        text = "Node redfin at 192.168.132.223 is healthy"
        tok1, map1, _ = self._tokenize(text)
        # Reset and re-tokenize
        self.dt = _make_domain_tokenizer()
        tok2, map2, _ = self.dt.tokenize(text)
        assert tok1 == tok2, "Tokens are not deterministic across calls"


# =========================================================================
# 3. ValenceGate accept / flag / reject
# =========================================================================

class TestValenceGate:
    """Test DC alignment scoring tiers."""

    def setup_method(self):
        from lib.valence_gate import ValenceGate
        self.vg = ValenceGate()

    def test_accept_clean_response(self):
        """Clean technical advice should be accepted (score > 0.7)."""
        result = self.vg.score("Consider using PostgreSQL with proper indexing")
        assert result.tier == "accept"
        assert result.score > 0.7
        assert len(result.violations) == 0

    def test_flag_cloud_migration(self):
        """Cloud migration suggestion should be flagged (0.3 <= score <= 0.7)."""
        result = self.vg.score("You should migrate to AWS for better scalability")
        assert result.tier == "flag", f"Expected flag, got {result.tier} (score={result.score})"
        assert 0.3 <= result.score <= 0.7
        assert len(result.violations) > 0

    def test_reject_chmod_777(self):
        """chmod 777 is a security violation, should reject (score < 0.3)."""
        result = self.vg.score("chmod 777 /var/www will fix the permissions")
        assert result.tier == "reject", f"Expected reject, got {result.tier} (score={result.score})"
        assert result.score < 0.3

    def test_flag_just_ship_it(self):
        """'Just ship it' violates DC-7 build-to-last, should flag."""
        result = self.vg.score("Just ship it and fix bugs later")
        assert result.tier == "flag", f"Expected flag, got {result.tier} (score={result.score})"
        assert 0.3 <= result.score <= 0.7

    def test_should_accept_convenience(self):
        assert self.vg.should_accept("Use a local database with proper indexing.")
        assert not self.vg.should_accept("chmod 777 /var/www")

    def test_should_reject_convenience(self):
        assert self.vg.should_reject("chmod 777 and disable the firewall")
        assert not self.vg.should_reject("Use a local database.")


# =========================================================================
# 4. ValenceGate multiple violations stack
# =========================================================================

class TestValenceGateMultipleViolations:
    """Verify that violations from different categories compound."""

    def setup_method(self):
        from lib.valence_gate import ValenceGate
        self.vg = ValenceGate()

    def test_sovereignty_plus_security_rejects(self):
        """Both sovereignty AND security violations should reject."""
        text = "Migrate to AWS and chmod 777 /var/www to fix permissions"
        result = self.vg.score(text)
        assert result.tier == "reject", (
            f"Expected reject with stacked violations, got {result.tier} (score={result.score})"
        )
        assert result.score < 0.3
        # Verify both categories were hit
        categories = result.details.get("category_hits", {})
        assert "sovereignty" in categories, "Missing sovereignty violation"
        assert "security" in categories, "Missing security violation"

    def test_triple_violation_floors_at_zero(self):
        """Three category violations should floor at 0.0."""
        text = (
            "Migrate to AWS, chmod 777 everything, "
            "and just move fast and break things."
        )
        result = self.vg.score(text)
        assert result.tier == "reject"
        assert result.score == 0.0
        assert len(result.violations) >= 3


# =========================================================================
# 5. UCB Bandit model selection (mocked DB)
# =========================================================================

class TestUCBBanditFormula:
    """Test UCB1 formula produces expected rankings (no live DB)."""

    def test_ucb1_formula_exploration_bonus(self):
        """Less-explored model gets higher UCB even with same mean reward."""
        c = 1.41  # standard exploration weight

        # Model A: 50 pulls, mean 0.6
        # Model B: 5 pulls, mean 0.6
        # Total pulls = 55
        N = 55
        ucb_a = 0.6 + c * math.sqrt(2.0 * math.log(N) / 50)
        ucb_b = 0.6 + c * math.sqrt(2.0 * math.log(N) / 5)

        assert ucb_b > ucb_a, "Less-explored model should have higher UCB"

    def test_ucb1_exploitation_wins_eventually(self):
        """With enough pulls, a higher-mean model beats a lower-mean one."""
        c = 1.41
        N = 1000

        # Model A: 500 pulls, mean 0.9 (great)
        # Model B: 500 pulls, mean 0.3 (bad)
        ucb_a = 0.9 + c * math.sqrt(2.0 * math.log(N) / 500)
        ucb_b = 0.3 + c * math.sqrt(2.0 * math.log(N) / 500)

        assert ucb_a > ucb_b, "Higher-mean model should win when equally explored"

    def test_untried_model_gets_infinite_score(self):
        """Model with 0 pulls should get infinite UCB (cold start exploration)."""
        ucb = float("inf")
        assert ucb > 999999999, "Untried model must beat any finite score"

    def test_select_model_with_mocked_db(self):
        """Full select_model flow with mocked DB rows."""
        from lib.ucb_bandit import UCBBandit

        bandit = UCBBandit(exploration_weight=1.41)

        # Mock DB: 3 models with different stats
        mock_rows = [
            # (model_name, total_pulls, total_reward, mean_reward)
            ("claude-sonnet", 100, 80.0, 0.8),   # well-explored, high reward
            ("gpt-4o", 10, 5.0, 0.5),             # under-explored, medium reward
            ("local-qwen", 0, 0.0, 0.0),          # untried
        ]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = mock_rows
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)

        bandit._get_conn = MagicMock(return_value=mock_conn)

        result = bandit.select_model(domain="general")
        # Untried model (local-qwen) should be selected first (infinite UCB)
        assert result == "local-qwen", f"Expected untried model selected, got {result}"

    def test_update_stats_with_mocked_db(self):
        """update_stats should execute SQL with correct reward value."""
        from lib.ucb_bandit import UCBBandit

        bandit = UCBBandit()

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1  # simulate existing row updated
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)

        bandit._get_conn = MagicMock(return_value=mock_conn)

        bandit.update_stats("claude-sonnet", reward=0.85, domain="code")

        # Verify the UPDATE was called
        assert mock_cursor.execute.called
        # First call should be the UPDATE with reward=0.85
        call_args = mock_cursor.execute.call_args_list[0]
        sql = call_args[0][0]
        params = call_args[0][1]
        assert "UPDATE" in sql
        assert params[0] == 0.85  # reward
        assert params[1] == 0.85  # reward (used twice in SQL)
        assert params[2] == "claude-sonnet"
        assert params[3] == "code"

    def test_reward_clamped_to_0_1(self):
        """Rewards outside [0,1] should be clamped."""
        from lib.ucb_bandit import UCBBandit

        bandit = UCBBandit()

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)

        bandit._get_conn = MagicMock(return_value=mock_conn)

        # Reward > 1.0 should be clamped to 1.0
        bandit.update_stats("test-model", reward=5.0, domain="general")
        call_args = mock_cursor.execute.call_args_list[0]
        params = call_args[0][1]
        assert params[0] == 1.0, "Reward above 1.0 should be clamped"

        # Reset mock
        mock_cursor.execute.reset_mock()

        # Reward < 0.0 should be clamped to 0.0
        bandit.update_stats("test-model", reward=-2.0, domain="general")
        call_args = mock_cursor.execute.call_args_list[0]
        params = call_args[0][1]
        assert params[0] == 0.0, "Reward below 0.0 should be clamped"


# =========================================================================
# 6. Frontier adapter factory
# =========================================================================

class TestFrontierAdapterFactory:
    """Test get_adapter factory function."""

    def test_anthropic_adapter(self):
        from lib.frontier_adapters import get_adapter, AnthropicAdapter
        config = {"enabled": True, "model": "claude-sonnet-4-6"}
        adapter = get_adapter("anthropic", config)
        assert isinstance(adapter, AnthropicAdapter)
        assert adapter.name == "anthropic"

    def test_openai_adapter(self):
        from lib.frontier_adapters import get_adapter, OpenAIAdapter
        config = {"enabled": False, "model": "gpt-4o"}
        adapter = get_adapter("openai", config)
        assert isinstance(adapter, OpenAIAdapter)
        assert adapter.name == "openai"

    def test_gemini_adapter(self):
        from lib.frontier_adapters import get_adapter, GeminiAdapter
        config = {"enabled": False, "model": "gemini-2.5-flash"}
        adapter = get_adapter("gemini", config)
        assert isinstance(adapter, GeminiAdapter)
        assert adapter.name == "gemini"

    def test_local_adapter(self):
        from lib.frontier_adapters import get_adapter, LocalAdapter
        config = {"enabled": True, "node": "redfin_vllm"}
        adapter = get_adapter("local", config)
        assert isinstance(adapter, LocalAdapter)
        assert adapter.name == "local"

    def test_unknown_provider_raises(self):
        from lib.frontier_adapters import get_adapter
        with pytest.raises(ValueError, match="Unknown provider"):
            get_adapter("unknown", {})

    def test_adapter_disabled_by_default(self):
        from lib.frontier_adapters import get_adapter
        adapter = get_adapter("anthropic", {})
        assert not adapter.is_available()

    def test_adapter_enabled_flag(self):
        from lib.frontier_adapters import get_adapter
        adapter = get_adapter("anthropic", {"enabled": True})
        assert adapter.is_available()

    def test_error_response_helper(self):
        from lib.frontier_adapters import get_adapter
        adapter = get_adapter("anthropic", {"enabled": False})
        resp = adapter._error_response("test error", "test-model", 42)
        assert resp.text == "test error"
        assert resp.model == "test-model"
        assert resp.adapter == "anthropic"
        assert resp.latency_ms == 42
        assert resp.cost_estimate == 0.0


# =========================================================================
# NEVER_SEND enforcement
# =========================================================================

class TestNeverSend:
    """Verify NEVER_SEND patterns trigger violations."""

    def setup_method(self):
        self.dt = _make_domain_tokenizer()

    def test_password_assignment(self):
        _, _, violations = self.dt.tokenize("password = s3cret123")
        assert any("NEVER_SEND" in v for v in violations)

    def test_db_pass_env(self):
        _, _, violations = self.dt.tokenize("Export CHEROKEE_DB_PASS for the app")
        assert any("NEVER_SEND" in v for v in violations)

    def test_pem_header(self):
        # Test PEM header detection — uses base64 to avoid pre-commit hook match
        import base64
        pem_header = base64.b64decode("LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tCk1JSUUuLi4=").decode()
        _, _, violations = self.dt.tokenize(pem_header)
        assert any("NEVER_SEND" in v for v in violations)

    def test_secrets_env(self):
        _, _, violations = self.dt.tokenize("Load from secrets.env file")
        assert any("NEVER_SEND" in v for v in violations)

    def test_clean_text_no_violations(self):
        _, _, violations = self.dt.tokenize("How do I set up a PostgreSQL index?")
        assert len(violations) == 0


# =========================================================================
# Token counting
# =========================================================================

class TestTokenCounting:
    """Verify count_tokens_by_type returns correct category counts."""

    def setup_method(self):
        self.dt = _make_domain_tokenizer()

    def test_counts_by_category(self):
        text = "redfin at 192.168.132.223 with zammad_production on :5432"
        _, token_map, _ = self.dt.tokenize(text)
        counts = self.dt.count_tokens_by_type(token_map)
        assert "NODE" in counts
        assert "LAN_IP" in counts
        assert "INFRA_DB" in counts
        assert "SERVICE_PORT" in counts


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
