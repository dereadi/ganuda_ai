"""
Real-Time Email Triage Wire for Chief PA.

Polls bluefin email_classifications table on a configurable interval
(default: 120s) and immediately pushes urgent actionable emails to Slack.
Non-urgent actionable emails are logged for the next daily briefing.

Privacy (Crawdad): No email body stored or transmitted to bmasass.
Only classification metadata: subject_preview, sender_domain, urgency_score.

Spec #4: Chief Personal Assistant (MVP)
Longhouse #b940f09b18605c97 (UNANIMOUS)
"""

import json
import logging
import os
import signal
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("chief_pa.email_triage")

# Database imports -- graceful degradation
try:
    import psycopg2
    import psycopg2.extras
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    logger.warning("psycopg2 not installed -- email triage wire unavailable")


class EmailTriageWire:
    """Real-time email triage poller and urgent alert dispatcher.

    Usage:
        wire = EmailTriageWire(
            db_config=config["database"],
            email_config=config["email"],
            slack_notifier=notifier,
        )
        wire.run()  # blocking loop, or
        wire.poll_once()  # single poll for testing

    State persistence: Tracks seen classification IDs in a JSON file
    to avoid duplicate alerts across daemon restarts.
    """

    DEFAULT_POLL_INTERVAL = 120  # seconds
    DEFAULT_URGENCY_THRESHOLD = 0.8
    DEFAULT_LOOKBACK_HOURS = 16
    DEFAULT_STATE_PATH = "~/.config/chief_pa/email_triage_state.json"

    def __init__(
        self,
        db_config: Dict[str, Any],
        email_config: Optional[Dict[str, Any]] = None,
        slack_notifier: Optional[Any] = None,
        poll_interval: Optional[int] = None,
        state_path: Optional[str] = None,
    ):
        self.db_config = db_config
        email_cfg = email_config or {}

        self.urgency_threshold = float(
            email_cfg.get("urgency_threshold", self.DEFAULT_URGENCY_THRESHOLD)
        )
        self.lookback_hours = int(
            email_cfg.get("lookback_hours", self.DEFAULT_LOOKBACK_HOURS)
        )
        self.max_actionable_display = int(
            email_cfg.get("max_actionable_display", 5)
        )
        self.poll_interval = poll_interval or int(
            email_cfg.get("poll_interval_seconds", self.DEFAULT_POLL_INTERVAL)
        )

        self.slack = slack_notifier
        self._running = False

        # State persistence
        raw_path = state_path or email_cfg.get(
            "state_path", self.DEFAULT_STATE_PATH
        )
        self.state_path = Path(os.path.expanduser(raw_path))
        self._seen_ids: Set[int] = set()
        self._load_state()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Blocking poll loop. Stops on SIGTERM/SIGINT."""
        if not DB_AVAILABLE:
            logger.error("Cannot start email triage wire: psycopg2 missing")
            return

        self._running = True
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        logger.info(
            "Email triage wire started (poll=%ds, urgency_threshold=%.2f)",
            self.poll_interval,
            self.urgency_threshold,
        )

        while self._running:
            try:
                self.poll_once()
            except Exception as e:
                logger.error("Poll cycle failed: %s", e)

            # Interruptible sleep
            for _ in range(self.poll_interval):
                if not self._running:
                    break
                time.sleep(1)

        self._save_state()
        logger.info("Email triage wire stopped")

    def poll_once(self) -> List[Dict[str, Any]]:
        """Single poll cycle. Returns list of newly alerted emails.

        Safe to call externally for testing or one-shot checks.
        """
        if not DB_AVAILABLE:
            logger.warning("psycopg2 not available, skipping poll")
            return []

        new_classifications = self._fetch_new_classifications()
        alerted: List[Dict[str, Any]] = []

        for row in new_classifications:
            row_id = row["id"]
            if row_id in self._seen_ids:
                continue

            self._seen_ids.add(row_id)

            classification = row.get("classification", "unknown")
            urgency = float(row.get("urgency_score", 0))
            sender = row.get("sender_domain", "unknown")
            subject = str(row.get("subject_preview", "(no subject)"))[:60]

            if classification == "actionable" and urgency >= self.urgency_threshold:
                # URGENT — immediate Slack push
                self._send_urgent_alert(subject, sender, urgency)
                alerted.append(row)
                logger.info(
                    "URGENT email alert sent: [%.2f] %s (%s)",
                    urgency, subject, sender,
                )
            elif classification == "actionable":
                # Non-urgent actionable — log for next briefing
                logger.info(
                    "Actionable email queued for briefing: [%.2f] %s (%s)",
                    urgency, subject, sender,
                )
            elif classification == "informational":
                logger.debug(
                    "Informational email skipped: %s (%s)", subject, sender,
                )
            # 'ignorable' emails are silently skipped

        # Persist state after each cycle
        if new_classifications:
            self._save_state()

        return alerted

    def stop(self) -> None:
        """Request graceful shutdown."""
        self._running = False

    # ------------------------------------------------------------------
    # DB queries
    # ------------------------------------------------------------------

    def _get_connection(self):
        """Create a new DB connection from config."""
        return psycopg2.connect(
            host=self.db_config.get("host", "192.168.132.222"),
            port=self.db_config.get("port", 5432),
            dbname=self.db_config.get("database", "zammad_production"),
            user=self.db_config.get("user", "claude"),
            password=self.db_config.get("password", ""),
            connect_timeout=self.db_config.get("connect_timeout", 10),
        )

    def _fetch_new_classifications(self) -> List[Dict[str, Any]]:
        """Fetch recent email classifications from bluefin.

        Returns rows not yet in self._seen_ids within the lookback window.
        Gracefully handles missing email_classifications table.
        """
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # Check if table exists (graceful if gmail daemon hasn't created it)
            cur.execute(
                "SELECT EXISTS ("
                "  SELECT 1 FROM information_schema.tables "
                "  WHERE table_name = 'email_classifications'"
                ")"
            )
            if not cur.fetchone()["exists"]:
                logger.warning(
                    "email_classifications table does not exist yet — "
                    "waiting for gmail_api_daemon to create it"
                )
                cur.close()
                return []

            since = datetime.now(timezone.utc) - timedelta(
                hours=self.lookback_hours
            )

            cur.execute(
                "SELECT id, sender_domain, subject_preview, "
                "       urgency_score, classification, classified_at "
                "FROM email_classifications "
                "WHERE classified_at >= %s "
                "ORDER BY urgency_score DESC "
                "LIMIT %s",
                (since, self.max_actionable_display * 10),
            )
            rows = cur.fetchall()
            cur.close()

            return [dict(r) for r in rows]

        except psycopg2.OperationalError as e:
            logger.warning("DB connection failed (bluefin reachable?): %s", e)
            return []
        except Exception as e:
            logger.error("Failed to fetch classifications: %s", e)
            return []
        finally:
            if conn:
                try:
                    conn.commit()  # explicit commit before close
                    conn.close()
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Slack alerts
    # ------------------------------------------------------------------

    def _send_urgent_alert(
        self, subject: str, sender_domain: str, urgency: float
    ) -> bool:
        """Push an urgent email alert to Slack.

        Uses category='email-triage' and urgent=True to bypass silent hours.
        """
        if not self.slack:
            logger.warning(
                "No Slack notifier configured, cannot send urgent alert"
            )
            return False

        urgency_pct = int(urgency * 100)
        text = (
            "URGENT EMAIL (score: "
            + str(urgency_pct)
            + "%)\n"
            + "Subject: "
            + subject
            + "\n"
            + "From: "
            + sender_domain
        )

        return self.slack.send_message(
            text=text,
            category="email-triage",
            urgent=True,
        )

    # ------------------------------------------------------------------
    # State persistence
    # ------------------------------------------------------------------

    def _load_state(self) -> None:
        """Load seen classification IDs from disk."""
        if not self.state_path.exists():
            logger.info("No prior triage state found, starting fresh")
            return

        try:
            with open(self.state_path, "r") as f:
                data = json.load(f)

            raw_ids = data.get("seen_ids", [])
            self._seen_ids = set(int(i) for i in raw_ids)
            logger.info(
                "Loaded %d seen classification IDs from state",
                len(self._seen_ids),
            )
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning("Corrupt state file, resetting: %s", e)
            self._seen_ids = set()
        except Exception as e:
            logger.warning("Failed to load state: %s", e)
            self._seen_ids = set()

    def _save_state(self) -> None:
        """Persist seen classification IDs to disk.

        Keeps only IDs from the current lookback window to prevent
        unbounded growth.
        """
        # Prune: only keep IDs that would still be in the lookback window.
        # We don't have timestamps per ID, so cap at a reasonable size.
        max_state_size = 5000
        if len(self._seen_ids) > max_state_size:
            # Keep the most recent (highest ID) entries
            sorted_ids = sorted(self._seen_ids)
            self._seen_ids = set(sorted_ids[-max_state_size:])

        try:
            self.state_path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
            with open(self.state_path, "w") as f:
                json.dump(
                    {
                        "seen_ids": sorted(self._seen_ids),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    f,
                )
        except Exception as e:
            logger.warning("Failed to save triage state: %s", e)

    # ------------------------------------------------------------------
    # Signal handling
    # ------------------------------------------------------------------

    def _handle_signal(self, signum, frame) -> None:
        """Handle SIGTERM/SIGINT for graceful shutdown."""
        logger.info("Received signal %d, shutting down...", signum)
        self._running = False


# ------------------------------------------------------------------
# Standalone entry point (for testing or direct invocation)
# ------------------------------------------------------------------
if __name__ == "__main__":
    import yaml

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(name)s %(levelname)s: %(message)s",
    )

    config_path = os.path.join(
        os.path.dirname(__file__), "config.yaml"
    )

    with open(config_path) as f:
        raw = f.read()
    # Expand env vars in config
    for key in ("CHEROKEE_DB_PASS", "SLACK_WEBHOOK_URL"):
        raw = raw.replace("${" + key + "}", os.environ.get(key, ""))
    config = yaml.safe_load(raw)

    from slack_notify import SlackNotifier

    notifier = SlackNotifier.from_config(config)

    wire = EmailTriageWire(
        db_config=config.get("database", {}),
        email_config=config.get("email", {}),
        slack_notifier=notifier,
    )

    logger.info("Running single poll cycle...")
    alerted = wire.poll_once()
    logger.info("Alerted on %d emails", len(alerted))