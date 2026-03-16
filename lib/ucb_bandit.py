#!/usr/bin/env python3
"""
UCB Bandit — Multi-armed bandit model selector for consultation ring.

Patent Brief #7: Tokenized Air-Gap Proxy
Council Vote: a3ee2a8066e04490 (UNANIMOUS)

UCB1 algorithm selects the best frontier model per domain.
Cold start: optimistic prior (1 success / 2 total) encourages exploration.
Postgres-backed via consultation_model_stats table.

DC-9: Penalizes rate-limited providers (waste heat).
"""

import logging
import math
from typing import Dict, List, Optional

import psycopg2

from lib.secrets_loader import get_db_config

logger = logging.getLogger("ucb_bandit")


class UCBBandit:
    """UCB1 model selector backed by consultation_model_stats."""

    def __init__(self, exploration_weight: float = 1.41):
        """
        Args:
            exploration_weight: UCB exploration parameter (sqrt(2) ≈ 1.41 is standard).
                Higher = more exploration, lower = more exploitation.
        """
        self.exploration_weight = exploration_weight
        self._db_config = None

    def _get_db(self):
        if self._db_config is None:
            self._db_config = get_db_config()
        return psycopg2.connect(**self._db_config)

    def select_model(self, domain: str = "general",
                     available_providers: Optional[List[str]] = None) -> Optional[dict]:
        """Select best model for domain using UCB1.

        Args:
            domain: Query domain (general, code, research, legal)
            available_providers: List of provider names with active adapters.
                If None, considers all enabled models.

        Returns:
            {"model_name": str, "provider": str, "ucb_score": float}
            or None if no models available.
        """
        conn = self._get_db()
        cur = conn.cursor()

        query = """
            SELECT model_name, provider, total_calls, successful_calls, total_reward
            FROM consultation_model_stats
            WHERE domain = %s AND enabled = true
        """
        params = [domain]

        if available_providers:
            placeholders = ",".join(["%s"] * len(available_providers))
            query += f" AND provider IN ({placeholders})"
            params.extend(available_providers)

        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            # Fall back to 'general' domain if specific domain has no stats
            if domain != "general":
                return self.select_model("general", available_providers)
            return None

        # Calculate total calls across all arms for UCB formula
        total_all = sum(r[2] for r in rows) or 1

        best = None
        best_score = -1

        for model_name, provider, total_calls, successful_calls, total_reward in rows:
            total_calls = int(total_calls)
            total_reward = float(total_reward)

            if total_calls == 0:
                # Untried model gets infinite UCB score (explore immediately)
                ucb = float("inf")
            else:
                # UCB1: mean reward + exploration bonus
                mean_reward = total_reward / total_calls
                exploration = self.exploration_weight * math.sqrt(
                    math.log(total_all) / total_calls
                )
                ucb = mean_reward + exploration

            if ucb > best_score:
                best_score = ucb
                best = {
                    "model_name": model_name,
                    "provider": provider,
                    "ucb_score": round(ucb, 4),
                }

        return best

    def update(self, model_name: str, domain: str, reward: float,
               latency_ms: int, cost: float, success: bool = True):
        """Update model stats after a consultation.

        Args:
            model_name: Model that was used
            domain: Query domain
            reward: Reward signal (0.0-1.0). From valence gate score.
            latency_ms: Response latency
            cost: Dollar cost of the call
            success: Whether the call succeeded (False for errors/rate limits)
        """
        conn = self._get_db()
        cur = conn.cursor()

        cur.execute("""
            UPDATE consultation_model_stats
            SET total_calls = total_calls + 1,
                successful_calls = successful_calls + CASE WHEN %s THEN 1 ELSE 0 END,
                total_reward = total_reward + %s,
                avg_latency_ms = (avg_latency_ms * total_calls + %s) / (total_calls + 1),
                total_cost = total_cost + %s,
                last_called = NOW(),
                updated_at = NOW()
            WHERE model_name = %s AND domain = %s
        """, (success, reward, latency_ms, cost, model_name, domain))

        if cur.rowcount == 0:
            # Model/domain combo doesn't exist — insert with this call as first
            cur.execute("""
                INSERT INTO consultation_model_stats
                    (model_name, provider, domain, total_calls, successful_calls,
                     total_reward, avg_latency_ms, total_cost, last_called)
                VALUES (%s, %s, %s, 1, %s, %s, %s, %s, NOW())
                ON CONFLICT (model_name, domain) DO UPDATE SET
                    total_calls = consultation_model_stats.total_calls + 1,
                    successful_calls = consultation_model_stats.successful_calls + CASE WHEN %s THEN 1 ELSE 0 END,
                    total_reward = consultation_model_stats.total_reward + %s,
                    avg_latency_ms = (consultation_model_stats.avg_latency_ms * consultation_model_stats.total_calls + %s) / (consultation_model_stats.total_calls + 1),
                    total_cost = consultation_model_stats.total_cost + %s,
                    last_called = NOW(),
                    updated_at = NOW()
            """, (model_name, "unknown", domain,
                  1 if success else 0, reward, latency_ms, cost,
                  success, reward, latency_ms, cost))

        conn.commit()
        cur.close()
        conn.close()

    def penalize_rate_limited(self, model_name: str, domain: str):
        """Penalize a rate-limited model. Counts as call with zero reward.

        DC-9: waste heat principle — rate limiting wastes energy.
        """
        self.update(model_name, domain, reward=0.0, latency_ms=0, cost=0.0, success=False)

    def get_stats(self, domain: str = None) -> List[dict]:
        """Get current stats for all models, optionally filtered by domain."""
        conn = self._get_db()
        cur = conn.cursor()

        if domain:
            cur.execute("""
                SELECT model_name, provider, domain, total_calls, successful_calls,
                       total_reward, avg_latency_ms, total_cost, enabled
                FROM consultation_model_stats
                WHERE domain = %s
                ORDER BY total_reward / GREATEST(total_calls, 1) DESC
            """, (domain,))
        else:
            cur.execute("""
                SELECT model_name, provider, domain, total_calls, successful_calls,
                       total_reward, avg_latency_ms, total_cost, enabled
                FROM consultation_model_stats
                ORDER BY domain, total_reward / GREATEST(total_calls, 1) DESC
            """)

        rows = cur.fetchall()
        cur.close()
        conn.close()

        return [
            {
                "model_name": r[0], "provider": r[1], "domain": r[2],
                "total_calls": r[3], "successful_calls": r[4],
                "mean_reward": round(r[5] / max(r[3], 1), 4),
                "avg_latency_ms": float(r[6] or 0),
                "total_cost": float(r[7] or 0),
                "enabled": r[8],
            }
            for r in rows
        ]
