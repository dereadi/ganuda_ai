"""
Google Calendar Integration for Chief PA.

Polls Google Calendar API v3 for upcoming events (next 24 hours).
Detects new, changed, and cancelled events since last poll.
Triggers urgent notifications for imminent meetings.

Uses OAuth2 with offline access -- same credential pattern as
/ganuda/email_daemon/gmail_api_daemon.py. Token stored in
~/.config/chief_pa/google_token.pickle (permission 600).

Auth flow: Run interactive OAuth2 authorization ONCE on bmasass
to generate the token. Token auto-refreshes thereafter.
Daemon runs headless after initial auth.

Polling interval: 5 minutes (configurable).
Urgency: Events within 30 minutes trigger immediate Slack push.
Dedup: Event ID tracking prevents duplicate notifications.
"""

import json
import logging
import os
import pickle
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Set, Tuple

logger = logging.getLogger("chief_pa.calendar")

# Google API imports -- these require google-api-python-client
# and google-auth-oauthlib on the runtime node (bmasass).
try:
    from google.auth.transport.requests import Request as GoogleAuthRequest
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build as google_build
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    logger.warning(
        "Google API libraries not installed. "
        "Install: pip install google-api-python-client google-auth-oauthlib"
    )


# Read-only calendar scope
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


class CalendarEvent:
    """Represents a Google Calendar event with relevant fields.

    Only stores metadata needed for notifications -- no full event
    descriptions stored locally (Crawdad: no PII on bmasass).
    """

    def __init__(
        self,
        event_id: str,
        title: str,
        start_time: datetime,
        end_time: datetime,
        location: str = "",
        attendee_count: int = 0,
        status: str = "confirmed",
        updated_at: str = "",
        is_all_day: bool = False,
    ):
        self.event_id = event_id
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.location = location
        self.attendee_count = attendee_count
        self.status = status
        self.updated_at = updated_at
        self.is_all_day = is_all_day

    def minutes_until_start(self) -> int:
        """Minutes until event starts. Negative if already started."""
        now = datetime.now(timezone.utc)
        delta = self.start_time - now
        return int(delta.total_seconds() / 60)

    def to_display_str(self) -> str:
        """Format for Slack display."""
        time_str = self.start_time.strftime("%I:%M %p")
        if self.is_all_day:
            time_str = "All day"
        parts = [time_str + " -- " + self.title]
        if self.location:
            parts.append("  Location: " + self.location)
        if self.attendee_count > 1:
            parts.append("  Attendees: " + str(self.attendee_count))
        return "\n".join(parts)


class GoogleCalendarPoller:
    """Polls Google Calendar API v3 for event changes.

    Tracks seen event IDs + update timestamps to detect:
    - New events (ID not seen before)
    - Changed events (ID seen but updated_at changed)
    - Cancelled events (previously seen ID now has status=cancelled)

    Usage:
        poller = GoogleCalendarPoller(config)
        poller.authenticate()
        new, changed, cancelled = poller.poll()
        upcoming = poller.get_upcoming_events(hours=24)
    """

    def __init__(
        self,
        credentials_path: str = "~/.config/chief_pa/google_credentials.json",
        token_path: str = "~/.config/chief_pa/google_token.pickle",
        state_path: str = "~/.config/chief_pa/calendar_state.json",
        poll_interval_seconds: int = 300,
        urgency_threshold_minutes: int = 30,
    ):
        self.credentials_path = os.path.expanduser(credentials_path)
        self.token_path = os.path.expanduser(token_path)
        self.state_path = os.path.expanduser(state_path)
        self.poll_interval_seconds = poll_interval_seconds
        self.urgency_threshold_minutes = urgency_threshold_minutes

        self._service = None
        self._known_events: Dict[str, str] = {}  # event_id -> updated_at
        self._load_state()

    def authenticate(self) -> bool:
        """Authenticate with Google Calendar API.

        Loads existing token or initiates OAuth2 flow.
        Same pattern as gmail_api_daemon.py.

        Returns:
            True if authenticated successfully, False otherwise.
        """
        if not GOOGLE_API_AVAILABLE:
            logger.error("Google API libraries not available")
            return False

        creds = None

        # Load existing token
        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, "rb") as f:
                    creds = pickle.load(f)
            except Exception as e:
                logger.warning("Failed to load token: %s", e)

        # Refresh if expired
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(GoogleAuthRequest())
                self._save_token(creds)
                logger.info("Token refreshed successfully")
            except Exception as e:
                logger.error("Token refresh failed: %s", e)
                creds = None

        # No valid creds -- need interactive auth
        if not creds or not creds.valid:
            if not os.path.exists(self.credentials_path):
                logger.error(
                    "No credentials file at %s. "
                    "Download from Google Cloud Console.",
                    self.credentials_path,
                )
                return False

            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
                self._save_token(creds)
                logger.info("New OAuth2 token obtained")
            except Exception as e:
                logger.error("OAuth2 flow failed: %s", e)
                return False

        # Build the Calendar API service
        try:
            self._service = google_build(
                "calendar", "v3", credentials=creds
            )
            logger.info("Google Calendar API authenticated")
            return True
        except Exception as e:
            logger.error("Failed to build Calendar service: %s", e)
            return False

    def poll(self) -> Tuple[List[CalendarEvent], List[CalendarEvent], List[str]]:
        """Poll for event changes since last check.

        Returns:
            Tuple of (new_events, changed_events, cancelled_event_ids).
        """
        if not self._service:
            logger.error("Not authenticated. Call authenticate() first.")
            return ([], [], [])

        try:
            events = self._fetch_events(hours_ahead=24)
        except Exception as e:
            logger.error("Failed to fetch events: %s", e)
            return ([], [], [])

        new_events = []
        changed_events = []
        current_ids: Set[str] = set()

        for event in events:
            current_ids.add(event.event_id)

            if event.event_id not in self._known_events:
                # New event
                new_events.append(event)
                self._known_events[event.event_id] = event.updated_at
            elif self._known_events[event.event_id] != event.updated_at:
                # Changed event
                changed_events.append(event)
                self._known_events[event.event_id] = event.updated_at

        # Detect cancelled events (previously known, no longer present)
        cancelled_ids = []
        for eid in list(self._known_events.keys()):
            if eid not in current_ids:
                cancelled_ids.append(eid)
                del self._known_events[eid]

        self._save_state()

        if new_events or changed_events or cancelled_ids:
            logger.info(
                "Poll results: %d new, %d changed, %d cancelled",
                len(new_events), len(changed_events), len(cancelled_ids),
            )

        return (new_events, changed_events, cancelled_ids)

    def get_upcoming_events(self, hours: int = 24) -> List[CalendarEvent]:
        """Get all events in the next N hours.

        Args:
            hours: How many hours ahead to look.

        Returns:
            List of CalendarEvent sorted by start time.
        """
        if not self._service:
            logger.error("Not authenticated")
            return []

        try:
            return self._fetch_events(hours_ahead=hours)
        except Exception as e:
            logger.error("Failed to fetch upcoming events: %s", e)
            return []

    def get_urgent_events(self) -> List[CalendarEvent]:
        """Get events starting within the urgency threshold.

        Returns:
            List of CalendarEvent starting within urgency_threshold_minutes.
        """
        all_events = self.get_upcoming_events(hours=1)
        urgent = []
        for event in all_events:
            if 0 < event.minutes_until_start() <= self.urgency_threshold_minutes:
                urgent.append(event)
        return urgent

    def _fetch_events(self, hours_ahead: int = 24) -> List[CalendarEvent]:
        """Fetch events from Google Calendar API.

        Args:
            hours_ahead: Hours into the future to query.

        Returns:
            List of CalendarEvent sorted by start time.
        """
        now = datetime.now(timezone.utc)
        time_min = now.isoformat()
        time_max = (now + timedelta(hours=hours_ahead)).isoformat()

        results = self._service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            maxResults=50,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = []
        for item in results.get("items", []):
            event = self._parse_event(item)
            if event:
                events.append(event)

        return events

    def _parse_event(self, item: Dict[str, Any]) -> Optional[CalendarEvent]:
        """Parse a Google Calendar API event item into CalendarEvent."""
        try:
            event_id = item.get("id", "")
            title = item.get("summary", "(No title)")
            status = item.get("status", "confirmed")
            updated_at = item.get("updated", "")
            location = item.get("location", "")

            # Parse start time
            start_raw = item.get("start", {})
            is_all_day = "date" in start_raw and "dateTime" not in start_raw

            if is_all_day:
                start_time = datetime.fromisoformat(
                    start_raw["date"]
                ).replace(tzinfo=timezone.utc)
            else:
                start_str = start_raw.get("dateTime", "")
                start_time = datetime.fromisoformat(start_str)
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc)

            # Parse end time
            end_raw = item.get("end", {})
            if is_all_day:
                end_time = datetime.fromisoformat(
                    end_raw.get("date", start_raw.get("date", ""))
                ).replace(tzinfo=timezone.utc)
            else:
                end_str = end_raw.get("dateTime", "")
                end_time = datetime.fromisoformat(end_str)
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=timezone.utc)

            # Attendee count
            attendees = item.get("attendees", [])
            attendee_count = len(attendees)

            return CalendarEvent(
                event_id=event_id,
                title=title,
                start_time=start_time,
                end_time=end_time,
                location=location,
                attendee_count=attendee_count,
                status=status,
                updated_at=updated_at,
                is_all_day=is_all_day,
            )
        except Exception as e:
            logger.warning("Failed to parse event %s: %s", item.get("id"), e)
            return None

    def _save_token(self, creds: Any) -> None:
        """Save OAuth2 token to disk with restricted permissions."""
        token_dir = os.path.dirname(self.token_path)
        os.makedirs(token_dir, mode=0o700, exist_ok=True)
        with open(self.token_path, "wb") as f:
            pickle.dump(creds, f)
        os.chmod(self.token_path, 0o600)

    def _save_state(self) -> None:
        """Save known event state to disk."""
        state_dir = os.path.dirname(self.state_path)
        os.makedirs(state_dir, mode=0o700, exist_ok=True)
        try:
            with open(self.state_path, "w") as f:
                json.dump(self._known_events, f)
        except Exception as e:
            logger.warning("Failed to save calendar state: %s", e)

    def _load_state(self) -> None:
        """Load known event state from disk."""
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r") as f:
                    self._known_events = json.load(f)
                logger.info(
                    "Loaded calendar state: %d known events",
                    len(self._known_events),
                )
            except Exception as e:
                logger.warning("Failed to load calendar state: %s", e)
                self._known_events = {}