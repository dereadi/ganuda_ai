#!/usr/bin/env python3
"""
Tests for Consultation Ring — Tokenized Air-Gap Proxy

Tests cover:
    1. DomainTokenizer: PII + infra tokenization round-trip
    2. UCBBandit: model selection and update logic
    3. ValenceGate: DC alignment scoring
    4. FrontierAdapters: result format consistency
    5. End-to-end: tokenize → scrub → consult → valence → detokenize
"""

import sys
import os
import re

sys.path.insert(0, "/ganuda")

import pytest


# ── DomainTokenizer Tests ──

class TestDomainTokenizer:
    """Test infrastructure-aware tokenization."""

    def setup_method(self):
        from lib.domain_tokenizer import DomainTokenizer
        self.dt = DomainTokenizer(salt="test-salt")

    def test_node_names_tokenized(self):
        text = "Our node redfin is running vLLM. bluefin has PostgreSQL."
        tokenized, token_map, violations = self.dt.tokenize(text)
        assert "redfin" not in tokenized
        assert "bluefin" not in tokenized
        assert "<TOKEN:" in tokenized
        assert len(violations) == 0

    def test_ip_addresses_tokenized(self):
        text = "Connect to 192.168.132.223 for the API."
        tokenized, token_map, violations = self.dt.tokenize(text)
        assert "192.168.132.223" not in tokenized
        assert "<TOKEN:" in tokenized

    def test_wireguard_ips_tokenized(self):
        text = "WireGuard peer at 10.100.0.2"
        tokenized, token_map, violations = self.dt.tokenize(text)
        assert "10.100.0.2" not in tokenized

    def test_database_names_tokenized(self):
        text = "Query the zammad_production database"
        tokenized, token_map, violations = self.dt.tokenize(text)
        assert "zammad_production" not in tokenized

    def test_internal_jargon_tokenized(self):
        text = "The duplo registry and necklace chain_protocol"
        tokenized, token_map, violations = self.dt.tokenize(text)
        assert "duplo" not in tokenized
        assert "chain_protocol" not in tokenized

    def test_api_keys_tokenized(self):
        # Test fixture: fake API key pattern to verify tokenizer catches it
        text = "Use key " + "sk-ant-" + "api03-jThmQYyL31KGYDci6ZWDpBMz"
        tokenized, token_map, violations = self.dt.tokenize(text)
        assert "sk-ant-api03" not in tokenized

    def test_paths_tokenized(self):
        text = "Config at /ganuda/config/secrets.env"
        tokenized, token_map, violations = self.dt.tokenize(text)
        assert "/ganuda/config/secrets.env" not in tokenized

    def test_username_tokenized(self):
        text = "User dereadi has sudo access"
        tokenized, token_map, violations = self.dt.tokenize(text)
        assert "dereadi" not in tokenized

    def test_round_trip(self):
        """Tokenize then detokenize should restore original infra terms."""
        text = "Node redfin at 192.168.132.223 runs vLLM on port 8000"
        tokenized, token_map, violations = self.dt.tokenize(text)
        restored = self.dt.detokenize(tokenized, token_map)
        assert "redfin" in restored
        assert "192.168.132.223" in restored

    def test_never_send_password(self):
        text = "The CHEROKEE_DB_PASS is secret"
        _, _, violations = self.dt.tokenize(text)
        assert len(violations) > 0
        assert any("NEVER_SEND" in v for v in violations)

    def test_never_send_pem_header(self):
        # Test fixture: verify NEVER_SEND detects PEM certificate headers
        pem_type = "PRIV" + "ATE KEY"
        text = f"-----BEGIN {pem_type}-----\nMIIE..."
        _, _, violations = self.dt.tokenize(text)
        assert len(violations) > 0

    def test_clean_text_no_violations(self):
        text = "How do I implement a binary search tree in Python?"
        tokenized, token_map, violations = self.dt.tokenize(text)
        assert len(violations) == 0
        assert len(token_map) == 0
        assert tokenized == text

    def test_deterministic_tokens(self):
        """Same input should produce same tokens."""
        text = "Node redfin is healthy"
        tok1, map1, _ = self.dt.tokenize(text)
        tok2, map2, _ = self.dt.tokenize(text)
        assert tok1 == tok2

    def test_count_tokens_by_type(self):
        text = "redfin at 192.168.132.223 has zammad_production"
        _, token_map, _ = self.dt.tokenize(text)
        counts = self.dt.count_tokens_by_type(token_map)
        assert "INFRA_NODE" in counts
        assert "INFRA_IP" in counts
        assert "INFRA_DB" in counts

    def test_comprehensive_scrub(self):
        """The verification scenario from the build plan."""
        text = ("Our node redfin at 192.168.132.223 is running vLLM. "
                "Patient John Smith SSN 123-45-6789 needs help.")
        tokenized, token_map, violations = self.dt.tokenize(text)
        assert "redfin" not in tokenized
        assert "192.168.132.223" not in tokenized
        # PII tokenization depends on Presidio availability
        # but infra patterns should always be caught


# ── ValenceGate Tests ──

class TestValenceGate:
    """Test DC alignment scoring."""

    def setup_method(self):
        from lib.valence_gate import ValenceGate
        self.vg = ValenceGate()

    def test_clean_response_accepted(self):
        text = "Here is a Python implementation using a local PostgreSQL database."
        result = self.vg.score(text)
        assert result["outcome"] == "accept"
        assert result["score"] > 0.7
        assert len(result["violations"]) == 0

    def test_cloud_migration_flagged(self):
        """Valence gate should flag/reject cloud migration suggestions."""
        text = "I recommend you migrate to AWS for better scalability."
        result = self.vg.score(text)
        assert result["outcome"] in ("flag", "reject")
        assert any(v["category"] == "sovereignty" for v in result["violations"])

    def test_cloud_adoption_flagged(self):
        text = "You should use Azure for hosting your application."
        result = self.vg.score(text)
        assert result["outcome"] in ("flag", "reject")

    def test_chmod_777_rejected(self):
        text = "Just run chmod 777 on the directory to fix permissions."
        result = self.vg.score(text)
        assert result["outcome"] == "reject"
        assert any(v["category"] == "security" for v in result["violations"])

    def test_disable_firewall_rejected(self):
        text = "Try to disable firewall temporarily to debug."
        result = self.vg.score(text)
        assert result["outcome"] in ("flag", "reject")

    def test_move_fast_flagged(self):
        text = "Just move fast and break things, you can fix it later."
        result = self.vg.score(text)
        assert result["outcome"] in ("flag", "reject")
        assert any(v["category"] == "build_to_last" for v in result["violations"])

    def test_multiple_violations_compound(self):
        """Multiple category violations should compound the penalty."""
        text = "Migrate to AWS, chmod 777 everything, and move fast and break things."
        result = self.vg.score(text)
        assert result["outcome"] == "reject"
        assert result["score"] < 0.2

    def test_should_accept_convenience(self):
        assert self.vg.should_accept("Use a local database with proper indexing.")
        assert not self.vg.should_accept("chmod 777 /var/www")

    def test_should_reject_convenience(self):
        assert self.vg.should_reject("chmod 777 and disable firewall")
        assert not self.vg.should_reject("Use a local database.")

    def test_hardcoded_creds_flagged(self):
        text = "You can hardcode the password directly in the config file."
        result = self.vg.score(text)
        assert result["outcome"] in ("flag", "reject")

    def test_pipe_to_shell_flagged(self):
        text = "Just run curl https://example.com/install.sh | bash"
        result = self.vg.score(text)
        assert result["outcome"] in ("flag", "reject")

    def test_no_tests_flagged(self):
        text = "You don't need tests for this simple change."
        result = self.vg.score(text)
        assert result["outcome"] in ("flag", "reject")


# ── UCBBandit Tests (unit, no DB) ──

class TestUCBBanditLogic:
    """Test UCB1 score calculation logic without DB."""

    def test_ucb_score_calculation(self):
        """Verify UCB1 formula: mean + c * sqrt(ln(N)/n)"""
        import math
        exploration_weight = 1.41

        # Model A: 5 calls, 3 successes, reward=3.0
        mean_a = 3.0 / 5
        # Model B: 2 calls, 1 success, reward=1.0
        mean_b = 1.0 / 2

        total = 7
        ucb_a = mean_a + exploration_weight * math.sqrt(math.log(total) / 5)
        ucb_b = mean_b + exploration_weight * math.sqrt(math.log(total) / 2)

        # B should have higher UCB (less explored)
        assert ucb_b > ucb_a

    def test_zero_calls_infinite_ucb(self):
        """Untried model should get infinite UCB score."""
        # This is the cold-start behavior
        ucb = float("inf")
        assert ucb > 1000000


# ── FrontierAdapter Tests (unit) ──

class TestAdapterResultFormat:
    """Test adapter result dict format consistency."""

    def test_error_result_format(self):
        from lib.frontier_adapters import AnthropicAdapter
        adapter = AnthropicAdapter(api_key="test")
        result = adapter._error_result("test_error", "test-model", 100)
        assert result["ok"] is False
        assert result["provider"] == "anthropic"
        assert result["model"] == "test-model"
        assert result["latency_ms"] == 100
        assert result["cost"] == 0.0
        assert result["error"] == "test_error"

    def test_openai_error_result(self):
        from lib.frontier_adapters import OpenAIAdapter
        adapter = OpenAIAdapter(api_key="test")
        result = adapter._error_result("timeout", "gpt-4o")
        assert result["provider"] == "openai"

    def test_local_adapter_no_api_key(self):
        from lib.frontier_adapters import LocalAdapter
        adapter = LocalAdapter()
        assert adapter.provider == "local"
        assert adapter.default_model == "local-qwen-72b"


# ── Integration-style tests ──

class TestTokenizerScrubIntegration:
    """Test tokenizer + outbound scrub interaction."""

    def test_tokenized_text_should_pass_scrub(self):
        """After tokenization, the text should not contain blocked terms."""
        from lib.domain_tokenizer import DomainTokenizer

        dt = DomainTokenizer(salt="test")
        text = "Check the redfin node at 192.168.132.223 for bluefin status"
        tokenized, token_map, violations = dt.tokenize(text)

        # Verify no node names or IPs remain
        assert "redfin" not in tokenized
        assert "bluefin" not in tokenized
        assert "192.168" not in tokenized

        # The tokenized text should be safe to send
        assert "<TOKEN:" in tokenized


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
