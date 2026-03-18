#!/usr/bin/env python3
"""
UCB1 Bandit — Multi-armed bandit model selector for Consultation Ring.

Patent Brief #7: Tokenized Air-Gap Proxy
Council Vote: a3ee2a8066e04490 (UNANIMOUS)
Jr Task: #1427

UCB1 algorithm selects the best frontier model per domain.
Cold start: optimistic prior (1 success / 2 total) encourages exploration.
Postgres-backed via consultation_model_stats table on bluefin.

DC-9: Penalizes rate-limited providers (waste heat).

Table schema (created by Jr #1424):
    consultation_model_stats(
        id, model_name (UNIQUE), domain, total_pulls, total_reward,
        mean_reward, last_selected_at, enabled, metadata, created_at, updated_at
    )
"""

import logging
import math
from typing import Dict, List, Optional

import psycopg2

from lib.secrets_loader import get_db_config

logger = logging.getLogger("consultation_ring.bandit")


class UCBBandit:
    """UCB1 model selector backed by consultation_model_stats."""

    def __init__(self, exploration_weight: float = 1.41):
        """
        Args:
            exploration_weight: UCB exploration parameter (sqrt(2) ~ 1.41 is standard).
                Higher = more exploration, lower = more exploitation.
        """
        self.exploration_weight = exploration_weight
        self._db_config = None

    def _get_conn(self):
        """Get a DB connection. Lazily loads credentials via secrets_loader."""
        if self._db_config is None:
            self._db_config = get_db_config()
        return psycopg2.connect(**self._db_config)

    def select_model(self, domain: str = "general") -> Optional[str]:
        """Select best model for domain using UCB1 formula.

        UCB1 = mean_reward + exploration_weight * sqrt(2 * ln(N) / n_i)
        where N = total pulls across all enabled models, n_i = pulls for model i.

        Only considers enabled models. Falls back to 'general' domain if
        no domain-specific models exist.

        Updates last_selected_at on the chosen model.

        Args:
            domain: Query domain (general, code, research, legal, etc.)

        Returns:
            model_name of the selected model, or None if no models available.
        """
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    # Fetch enabled models for this domain
                    cur.execute(
                        """
                        SELECT model_name, total_pulls, total_reward, mean_reward
                        FROM consultation_model_stats
                        WHERE domain = %s AND enabled = true
                        """,
                        (domain,),
                    )
                    rows = cur.fetchall()

                    # Domain fallback: if no models for requested domain, try general
                    if not rows and domain != "general":
                        logger.info(
                            "No models for domain '%s', falling back to 'general'",
                            domain,
                        )
                        cur.execute(
                            """
                            SELECT model_name, total_pulls, total_reward, mean_reward
                            FROM consultation_model_stats
                            WHERE domain = 'general' AND enabled = true
                            """,
                        )
                        rows = cur.fetchall()

                    if not rows:
                        logger.warning("No enabled models found for any domain")
                        return None

                    # Total pulls across all arms (for UCB1 denominator)
                    total_all = sum(r[1] for r in rows) or 1

                    best_model = None
                    best_score = -1.0

                    for model_name, total_pulls, total_reward, mean_reward in rows:
                        total_pulls = int(total_pulls)

                        if total_pulls == 0:
                            # Untried arm gets infinite score (explore immediately)
                            ucb = float("inf")
                        else:
                            # UCB1: mean_reward + c * sqrt(2 * ln(N) / n_i)
                            mr = float(total_reward) / total_pulls
                            exploration = self.exploration_weight * math.sqrt(
                                2.0 * math.log(total_all) / total_pulls
                            )
                            ucb = mr + exploration

                        if ucb > best_score:
                            best_score = ucb
                            best_model = model_name

                    # Update last_selected_at for the chosen model
                    if best_model:
                        cur.execute(
                            """
                            UPDATE consultation_model_stats
                            SET last_selected_at = NOW(), updated_at = NOW()
                            WHERE model_name = %s
                            """,
                            (best_model,),
                        )
                        logger.info(
                            "UCB1 selected model='%s' (score=%.4f, domain='%s')",
                            best_model,
                            best_score,
                            domain,
                        )

                    return best_model
        finally:
            conn.commit()  # explicit commit before close
            conn.close()

    def update_stats(
        self, model_name: str, reward: float, domain: str = "general"
    ) -> None:
        """Record outcome of a consultation.

        Args:
            model_name: The model that was consulted.
            reward: 0.0-1.0 reward signal (from valence gate score).
            domain: Domain the consultation was for.

        Updates total_pulls, total_reward, mean_reward.
        If model/domain combo doesn't exist, inserts a new row.
        """
        reward = max(0.0, min(1.0, float(reward)))  # clamp to [0, 1]

        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE consultation_model_stats
                        SET total_pulls = total_pulls + 1,
                            total_reward = total_reward + %s,
                            mean_reward = (total_reward + %s) / (total_pulls + 1),
                            updated_at = NOW()
                        WHERE model_name = %s AND domain = %s
                        """,
                        (reward, reward, model_name, domain),
                    )

                    if cur.rowcount == 0:
                        # Model/domain doesn't exist — insert with this as first pull
                        # (on top of the optimistic prior logic: seeded rows already have
                        # 2 pulls and 1.0 reward; new rows start fresh)
                        cur.execute(
                            """
                            INSERT INTO consultation_model_stats
                                (model_name, domain, total_pulls, total_reward,
                                 mean_reward, enabled, metadata)
                            VALUES (%s, %s, 1, %s, %s, true, '{}')
                            ON CONFLICT (model_name) DO UPDATE SET
                                total_pulls = consultation_model_stats.total_pulls + 1,
                                total_reward = consultation_model_stats.total_reward + %s,
                                mean_reward = (consultation_model_stats.total_reward + %s)
                                    / (consultation_model_stats.total_pulls + 1),
                                updated_at = NOW()
                            """,
                            (
                                model_name, domain, reward, reward,
                                reward, reward,
                            ),
                        )

                    logger.info(
                        "Updated stats: model='%s' domain='%s' reward=%.3f",
                        model_name,
                        domain,
                        reward,
                    )
        finally:
            conn.commit()  # explicit commit before close
            conn.close()

    def penalize_rate_limited(self, model_name: str, domain: str = "general") -> None:
        """Penalize a rate-limited model. Counts as pull with zero reward.

        DC-9: waste heat principle — rate limiting wastes energy.
        """
        self.update_stats(model_name, reward=0.0, domain=domain)
        logger.info("Penalized rate-limited model='%s' domain='%s'", model_name, domain)

    def get_stats(self, domain: Optional[str] = None) -> List[Dict]:
        """Return current stats for all models, optionally filtered by domain.

        Args:
            domain: If provided, filter to this domain. Otherwise return all.

        Returns:
            List of dicts with model stats, ordered by mean_reward descending.
        """
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                if domain:
                    cur.execute(
                        """
                        SELECT model_name, domain, total_pulls, total_reward,
                               mean_reward, last_selected_at, enabled, metadata
                        FROM consultation_model_stats
                        WHERE domain = %s
                        ORDER BY mean_reward DESC
                        """,
                        (domain,),
                    )
                else:
                    cur.execute(
                        """
                        SELECT model_name, domain, total_pulls, total_reward,
                               mean_reward, last_selected_at, enabled, metadata
                        FROM consultation_model_stats
                        ORDER BY domain, mean_reward DESC
                        """,
                    )

                rows = cur.fetchall()
                return [
                    {
                        "model_name": r[0],
                        "domain": r[1],
                        "total_pulls": r[2],
                        "total_reward": float(r[3]),
                        "mean_reward": float(r[4]),
                        "last_selected_at": r[5].isoformat() if r[5] else None,
                        "enabled": r[6],
                        "metadata": r[7] or {},
                    }
                    for r in rows
                ]
        finally:
            conn.commit()  # explicit commit before close
            conn.close()
