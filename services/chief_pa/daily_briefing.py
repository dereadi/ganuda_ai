"""
Daily Briefing Generator for Chief PA.

Assembles the morning digest from multiple data sources:
- Today's calendar events (from google_calendar module)
- Overnight cluster activity (thermal memory count + highlights from bluefin)
- Actionable emails (from gmail_api_daemon classification data)
- Pending kanban items (from duyuktv_tickets on bluefin)
- Recent council votes (from council_votes on bluefin)

Routes assembled data through Tier 1 Reflex for natural language summary.
Pushes final briefing to Slack via slack_notify.

Schedule: 0900 Central (configurable).
Fallback: On failure, sends cached last-good briefing with STALE warning.
"""

import json
import logging
from lib.harness.core import HarnessRequest
from lib.harness.config import load_harness_config
from lib.harness.escalation import EscalationEngine
from lib.harness.tier1_reflex import Tier1Reflex
from lib.harness.tier2_deliberation import Tier2Deliberation
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from zoneinfo import ZoneInfo

logger = logging.getLogger("chief_pa.briefing")

# Database imports -- optional, only needed when querying bluefin
try:
    import psycopg2
    import psycopg2.extras
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    logger.warning("psycopg2 not installed -- cluster data sources unavailable")


class DailyBriefingGenerator:
    """Assembles and delivers the Chief's morning briefing.

    Usage:
        generator = DailyBriefingGenerator(config)
        generator.generate_and_send()
        generator.publish_to_web()  # Also publishes HTML to ganuda.us/briefing.html

    The briefing has five sections:
    1. Summary -- LLM-generated "What's on your plate today"
    2. Calendar -- Today's events from Google Calendar
    3. Emails -- Actionable emails from gmail classification
    4. Cluster -- Overnight federation activity highlights
    5. Kanban -- Open/blocked items needing attention
    """

    def __init__(
        self,
        db_config: Optional[Dict[str, Any]] = None,
        tier1_handler: Optional[Any] = None,
        slack_notifier: Optional[Any] = None,
        calendar_poller: Optional[Any] = None,
        timezone_str: str = "America/Chicago",
        cache_path: str = "~/.config/chief_pa/last_briefing.json",
    ):
        self.db_config = db_config or {}
        self.tier1 = tier1_handler
        self.slack = slack_notifier
        self.calendar = calendar_poller
        self.tz = ZoneInfo(timezone_str)
        self.cache_path = os.path.expanduser(cache_path)

    def generate_and_send(self) -> bool:
        """Generate the full briefing and send to Slack.

        Returns:
            True if briefing sent successfully, False otherwise.
        """
        start_time = time.time()
        logger.info("Generating daily briefing...")

        try:
            # Gather data from all sources
            calendar_section = self._gather_calendar()
            cluster_section = self._gather_cluster_activity()
            email_section = self._gather_emails()
            kanban_section = self._gather_kanban()

            # Build raw data summary for Tier 1
            raw_data = self._assemble_raw_data(
                calendar_section, cluster_section,
                email_section, kanban_section,
            )

            # Route through Tier 1 for natural language summary
            summary = self._generate_summary(raw_data)

            # Send to Slack
            if self.slack:
                ok = self.slack.send_briefing(
                    calendar_section=calendar_section,
                    cluster_section=cluster_section,
                    email_section=email_section,
                    kanban_section=kanban_section,
                    summary=summary,
                )
            else:
                logger.warning("No Slack notifier configured, briefing not sent")
                ok = False

            if ok:
                # Cache successful briefing
                self._cache_briefing({
                    "calendar": calendar_section,
                    "cluster": cluster_section,
                    "email": email_section,
                    "kanban": kanban_section,
                    "summary": summary,
                    "generated_at": datetime.now(self.tz).isoformat(),
                })

            elapsed = time.time() - start_time
            logger.info(
                "Briefing %s in %.1fs",
                "sent" if ok else "failed",
                elapsed,
            )
            return ok

        except Exception as e:
            logger.error("Briefing generation failed: %s", e)
            # Attempt to send cached briefing
            return self._send_cached_briefing()

    def _gather_calendar(self) -> str:
        """Gather today's calendar events."""
        if not self.calendar:
            return "Calendar integration not configured."

        try:
            events = self.calendar.get_upcoming_events(hours=16)
            if not events:
                return "No events on the calendar today."

            lines = []
            for event in events:
                lines.append(event.to_display_str())

            return "\n".join(lines)
        except Exception as e:
            logger.warning("Failed to gather calendar: %s", e)
            return "Calendar data unavailable."

    def _gather_cluster_activity(self) -> str:
        """Gather overnight cluster activity from thermal memory."""
        if not DB_AVAILABLE or not self.db_config:
            return "Cluster data unavailable (no DB connection)."

        try:
            conn = psycopg2.connect(
                host=self.db_config.get("host", "192.168.132.222"),
                port=self.db_config.get("port", 5432),
                dbname=self.db_config.get("database", "zammad_production"),
                user=self.db_config.get("user", "claude"),
                password=self.db_config.get("password", ""),
                connect_timeout=10,
            )
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # Time window: last 16 hours (overnight)
            since = datetime.now(timezone.utc) - timedelta(hours=16)

            # Count thermal memories
            cur.execute(
                "SELECT COUNT(*) as cnt FROM thermal_memory_archive "
                "WHERE created_at >= %s",
                (since,),
            )
            thermal_count = cur.fetchone()["cnt"]

            # High-temperature thermals (alerts)
            cur.execute(
                "SELECT original_content FROM thermal_memory_archive "
                "WHERE created_at >= %s AND temperature_score >= 90 "
                "ORDER BY temperature_score DESC LIMIT 3",
                (since,),
            )
            hot_thermals = cur.fetchall()

            # Jr task completions
            cur.execute(
                "SELECT COUNT(*) as cnt FROM jr_work_queue "
                "WHERE completed_at >= %s AND status = 'completed'",
                (since,),
            )
            jr_completed = cur.fetchone()["cnt"]

            # Jr task failures
            cur.execute(
                "SELECT COUNT(*) as cnt FROM jr_work_queue "
                "WHERE updated_at >= %s AND status = 'failed'",
                (since,),
            )
            jr_failed = cur.fetchone()["cnt"]

            # Recent council votes
            cur.execute(
                "SELECT COUNT(*) as cnt FROM council_votes "
                "WHERE created_at >= %s",
                (since,),
            )
            vote_count = cur.fetchone()["cnt"]

            cur.close()
            conn.close()

            lines = [
                "Thermal memories (16h): " + str(thermal_count),
                "Jr tasks completed: " + str(jr_completed),
                "Jr tasks failed: " + str(jr_failed),
                "Council votes: " + str(vote_count),
            ]

            if hot_thermals:
                lines.append("")
                lines.append("Hot thermals (temp >= 90):")
                for t in hot_thermals:
                    content = str(t["original_content"])[:120]
                    lines.append("  - " + content)

            return "\n".join(lines)

        except Exception as e:
            logger.warning("Failed to gather cluster activity: %s", e)
            return "Cluster data query failed."

    def _gather_emails(self) -> str:
        """Gather actionable email summary.

        Queries the email classification data from bluefin.
        No email bodies -- metadata only (Crawdad: no PII on bmasass).
        """
        if not DB_AVAILABLE or not self.db_config:
            return "Email data unavailable."

        try:
            conn = psycopg2.connect(
                host=self.db_config.get("host", "192.168.132.222"),
                port=self.db_config.get("port", 5432),
                dbname=self.db_config.get("database", "zammad_production"),
                user=self.db_config.get("user", "claude"),
                password=self.db_config.get("password", ""),
                connect_timeout=10,
            )
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            since = datetime.now(timezone.utc) - timedelta(hours=16)

            # Check if email_classifications table exists
            cur.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_name = 'email_classifications')"
            )
            if not cur.fetchone()["exists"]:
                cur.close()
                conn.close()
                return "Email classification table not yet created."

            cur.execute(
                "SELECT sender_domain, subject_preview, urgency_score, classification "
                "FROM email_classifications "
                "WHERE classified_at >= %s AND classification = 'actionable' "
                "ORDER BY urgency_score DESC LIMIT 5",
                (since,),
            )
            emails = cur.fetchall()

            cur.close()
            conn.close()

            if not emails:
                return "No actionable emails overnight."

            lines = [str(len(emails)) + " actionable email(s):"]
            for em in emails:
                urgency = em.get("urgency_score", 0)
                domain = em.get("sender_domain", "unknown")
                subject = em.get("subject_preview", "(no subject)")[:60]
                urgency_label = "HIGH" if urgency >= 0.8 else "normal"
                lines.append(
                    "  [" + urgency_label + "] " + subject
                    + " (from: " + domain + ")"
                )

            return "\n".join(lines)

        except Exception as e:
            logger.warning("Failed to gather emails: %s", e)
            return "Email data query failed."

    def _gather_kanban(self) -> str:
        """Gather pending kanban items needing attention."""
        if not DB_AVAILABLE or not self.db_config:
            return "Kanban data unavailable."

        try:
            conn = psycopg2.connect(
                host=self.db_config.get("host", "192.168.132.222"),
                port=self.db_config.get("port", 5432),
                dbname=self.db_config.get("database", "zammad_production"),
                user=self.db_config.get("user", "claude"),
                password=self.db_config.get("password", ""),
                connect_timeout=10,
            )
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # Blocked items (highest priority)
            cur.execute(
                "SELECT title FROM duyuktv_tickets "
                "WHERE status = 'blocked' "
                "ORDER BY sacred_fire_priority DESC NULLS LAST LIMIT 5"
            )
            blocked = cur.fetchall()

            # Open items count
            cur.execute(
                "SELECT COUNT(*) as cnt FROM duyuktv_tickets "
                "WHERE status = 'open'"
            )
            open_count = cur.fetchone()["cnt"]

            # In-progress count
            cur.execute(
                "SELECT COUNT(*) as cnt FROM duyuktv_tickets "
                "WHERE status = 'in_progress'"
            )
            in_progress = cur.fetchone()["cnt"]

            cur.close()
            conn.close()

            lines = [
                "Open: " + str(open_count) + " | In Progress: " + str(in_progress),
            ]

            if blocked:
                lines.append("Blocked (" + str(len(blocked)) + "):")
                for item in blocked:
                    lines.append("  - " + str(item["title"])[:80])
            else:
                lines.append("No blocked items.")

            return "\n".join(lines)

        except Exception as e:
            logger.warning("Failed to gather kanban: %s", e)
            return "Kanban data query failed."

    def _assemble_raw_data(
        self,
        calendar: str,
        cluster: str,
        email: str,
        kanban: str,
    ) -> str:
        """Assemble raw data sections into a prompt for Tier 1."""
        now = datetime.now(self.tz)
        return (
            "Today is " + now.strftime("%A, %B %d, %Y") + ".\n\n"
            "Here is the Chief's morning data. Please write a brief, "
            "natural-language summary paragraph titled "
            "'What's on your plate today, Chief?' that highlights "
            "the most important items. Be direct and concise.\n\n"
            "CALENDAR:\n" + calendar + "\n\n"
            "CLUSTER ACTIVITY (overnight):\n" + cluster + "\n\n"
            "ACTIONABLE EMAILS:\n" + email + "\n\n"
            "KANBAN:\n" + kanban
        )

    def _generate_summary(self, raw_data: str) -> str:
        """Route raw data through Tier 1 for natural language summary."""
        if not self.tier1:
            logger.warning("No Tier 1 handler, using raw data as summary")
            return "Summary generation unavailable. See sections below."

        try:
            from lib.harness.core import HarnessRequest

            request = HarnessRequest(
                query=raw_data,
                context={"purpose": "daily_briefing"},
                user_id="chief",
            )

            result = self.tier1.handle(request)
            if result.confidence > 0:
                return result.answer
            else:
                logger.warning(
                    "Tier 1 returned zero confidence for briefing summary"
                )
                return "Summary generation returned low confidence. See raw sections."

        except Exception as e:
            logger.error("Tier 1 summary generation failed: %s", e)
            return "Summary generation failed. See raw sections below."

    def _cache_briefing(self, data: Dict[str, Any]) -> None:
        """Cache successful briefing for fallback use."""
        cache_dir = os.path.dirname(self.cache_path)
        os.makedirs(cache_dir, mode=0o700, exist_ok=True)
        try:
            with open(self.cache_path, "w") as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning("Failed to cache briefing: %s", e)

    def _send_cached_briefing(self) -> bool:
        """Send the last cached briefing with a STALE warning."""
        if not os.path.exists(self.cache_path):
            logger.error("No cached briefing available")
            if self.slack:
                self.slack.send_message(
                    text="Daily briefing generation FAILED and no cache available. "
                         "Check federation health.",
                    category="cluster-alert",
                    urgent=True,
                )
            return False

        try:
            with open(self.cache_path, "r") as f:
                cached = json.load(f)

            generated_at = cached.get("generated_at", "unknown")
            stale_warning = (
                "WARNING: This is a STALE briefing from " + generated_at
                + ". Live briefing generation failed. "
                "Check federation connectivity."
            )

            if self.slack:
                return self.slack.send_briefing(
                    calendar_section=cached.get("calendar", ""),
                    cluster_section=cached.get("cluster", ""),
                    email_section=cached.get("email", ""),
                    kanban_section=cached.get("kanban", ""),
                    summary=stale_warning + "\n\n" + cached.get("summary", ""),
                )
            return False

        except Exception as e:
            logger.error("Failed to send cached briefing: %s", e)
            return False
# Harness integration (DC-10)
_harness_engine = None

def _get_harness():
    global _harness_engine
    if _harness_engine is not None:
        return _harness_engine
    config = load_harness_config()
    engine = EscalationEngine(config)
    if config.tier1.enabled:
        engine.register_tier(1, Tier1Reflex(config.tier1))
    if config.tier2.enabled:
        engine.register_tier(2, Tier2Deliberation(config.tier2))
    _harness_engine = engine
    return _harness_engine


def harness_query(query, context=None, user_id="chief_pa"):
    """Route a query through the graduated harness."""
    engine = _get_harness()
    req = HarnessRequest(
        query=query,
        context=context or {},
        user_id=user_id,
    )
    resp = engine.handle_request(req)
    return resp.answer, resp.tier_used, resp.confidence

