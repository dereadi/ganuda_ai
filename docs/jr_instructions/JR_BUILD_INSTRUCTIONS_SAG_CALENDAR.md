# Jr Build Instructions: SAG Calendar with iCloud Sync
## Priority: MEDIUM - Post-Launch Enhancement

---

## Objective

Implement a Calendar view in SAG Unified Interface that:
1. Displays events in a monthly/weekly/daily calendar grid
2. Syncs with iPhone calendar via iCloud CalDAV
3. Shows today's events and upcoming items at a glance
4. Allows viewing event details from SAG
5. Optionally integrates AI assistance for scheduling

---

## Current State

- ✅ Calendar nav item added to SAG sidebar
- ✅ Basic calendar HTML structure exists (`#calendar-view`)
- ✅ Basic JavaScript calendar rendering exists
- ❌ Calendar CSS styling NOT complete
- ❌ API endpoints NOT implemented
- ❌ iCloud CalDAV integration NOT implemented

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    SAG Web Interface                     │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Calendar View                       │    │
│  │  ┌──────────┐  ┌───────────┐  ┌────────────┐   │    │
│  │  │Month Grid│  │Event List │  │Event Detail│   │    │
│  │  └────┬─────┘  └─────┬─────┘  └─────┬──────┘   │    │
│  └───────┼──────────────┼──────────────┼──────────┘    │
└──────────┼──────────────┼──────────────┼───────────────┘
           │              │              │
           ▼              ▼              ▼
┌─────────────────────────────────────────────────────────┐
│                    Flask API Layer                       │
│  /api/calendar/events  /api/calendar/sync               │
└─────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────┐
│                   calendar.py Module                     │
│  - iCloud CalDAV client                                 │
│  - Event caching (Redis)                                │
│  - Event parsing                                        │
└─────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────┐
│             iCloud CalDAV Server                         │
│  caldav.icloud.com                                      │
│  (Requires App-Specific Password)                       │
└─────────────────────────────────────────────────────────┘
```

---

## iCloud CalDAV Integration

### Prerequisites

1. **Apple ID with 2FA enabled** (required for app-specific passwords)
2. **App-Specific Password**: Generated at https://appleid.apple.com/account/manage
3. **Python caldav library**: `pip install caldav`

### iCloud CalDAV Connection Details

```
Server: caldav.icloud.com
Principal URL: https://caldav.icloud.com/<user_id>/calendars/
Auth: Basic Auth with Apple ID + App-Specific Password
```

### Task 1: Create calendar.py Module

Location: `/home/dereadi/sag_unified_interface/calendar_sync.py`

```python
"""SAG Calendar Sync Module - iCloud CalDAV Integration"""
import caldav
import redis
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from icalendar import Calendar as iCalendar

logger = logging.getLogger(__name__)

# Redis for caching
try:
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    REDIS_AVAILABLE = True
except:
    REDIS_AVAILABLE = False
    redis_client = None


def get_icloud_config() -> Optional[Dict]:
    """Get iCloud credentials from Redis or config"""
    if REDIS_AVAILABLE:
        config = redis_client.get("sag:calendar:icloud_config")
        if config:
            return json.loads(config)
    return None


def set_icloud_config(config: Dict) -> bool:
    """Store iCloud credentials (encrypted in production)"""
    if REDIS_AVAILABLE:
        # WARNING: In production, encrypt credentials before storing
        redis_client.set("sag:calendar:icloud_config", json.dumps(config))
        return True
    return False


def connect_to_icloud() -> Optional[caldav.DAVClient]:
    """Establish CalDAV connection to iCloud"""
    config = get_icloud_config()
    if not config:
        logger.error("iCloud not configured")
        return None

    try:
        client = caldav.DAVClient(
            url="https://caldav.icloud.com",
            username=config["apple_id"],
            password=config["app_password"]  # App-specific password
        )
        return client
    except Exception as e:
        logger.error(f"iCloud connection failed: {e}")
        return None


def get_calendars() -> List[Dict]:
    """Get list of available calendars from iCloud"""
    client = connect_to_icloud()
    if not client:
        return []

    try:
        principal = client.principal()
        calendars = principal.calendars()

        return [
            {
                "id": str(cal.id) if cal.id else cal.url,
                "name": cal.name or "Unnamed Calendar",
                "url": str(cal.url)
            }
            for cal in calendars
        ]
    except Exception as e:
        logger.error(f"Failed to fetch calendars: {e}")
        return []


def get_events(year: int, month: int, calendar_id: Optional[str] = None) -> List[Dict]:
    """Fetch events for a specific month"""

    # Check cache first
    cache_key = f"sag:calendar:events:{year}:{month}"
    if REDIS_AVAILABLE:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

    client = connect_to_icloud()
    if not client:
        # Return mock data if not configured
        return get_mock_events(year, month)

    try:
        principal = client.principal()
        calendars = principal.calendars()

        # Date range for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        events = []
        for cal in calendars:
            if calendar_id and str(cal.id) != calendar_id:
                continue

            try:
                cal_events = cal.date_search(
                    start=start_date,
                    end=end_date,
                    expand=True
                )

                for event in cal_events:
                    parsed = parse_event(event, cal.name)
                    if parsed:
                        events.append(parsed)
            except Exception as e:
                logger.warning(f"Error fetching from calendar {cal.name}: {e}")

        # Sort by start time
        events.sort(key=lambda e: e.get("start", ""))

        # Cache for 5 minutes
        if REDIS_AVAILABLE:
            redis_client.setex(cache_key, 300, json.dumps(events))

        return events

    except Exception as e:
        logger.error(f"Failed to fetch events: {e}")
        return get_mock_events(year, month)


def parse_event(caldav_event, calendar_name: str) -> Optional[Dict]:
    """Parse a CalDAV event into our format"""
    try:
        ical = iCalendar.from_ical(caldav_event.data)

        for component in ical.walk():
            if component.name == "VEVENT":
                start = component.get("dtstart")
                end = component.get("dtend")

                # Handle all-day events vs timed events
                if start:
                    start_dt = start.dt
                    if hasattr(start_dt, "isoformat"):
                        start_str = start_dt.isoformat()
                    else:
                        start_str = str(start_dt)
                else:
                    start_str = ""

                if end:
                    end_dt = end.dt
                    if hasattr(end_dt, "isoformat"):
                        end_str = end_dt.isoformat()
                    else:
                        end_str = str(end_dt)
                else:
                    end_str = start_str

                return {
                    "id": str(component.get("uid", "")),
                    "title": str(component.get("summary", "Untitled")),
                    "start": start_str,
                    "end": end_str,
                    "location": str(component.get("location", "")),
                    "description": str(component.get("description", "")),
                    "calendar": calendar_name,
                    "all_day": not hasattr(start.dt, "hour") if start else False
                }

        return None
    except Exception as e:
        logger.error(f"Failed to parse event: {e}")
        return None


def get_mock_events(year: int, month: int) -> List[Dict]:
    """Return mock events when iCloud not configured"""
    today = datetime.now()

    return [
        {
            "id": "mock-1",
            "title": "Configure iCloud Calendar",
            "start": today.replace(hour=10, minute=0).isoformat(),
            "end": today.replace(hour=11, minute=0).isoformat(),
            "location": "SAG Settings",
            "description": "Go to Settings > Calendar to connect your iCloud account",
            "calendar": "Demo",
            "all_day": False
        },
        {
            "id": "mock-2",
            "title": "Council Stand-up",
            "start": (today + timedelta(days=1)).replace(hour=9, minute=0).isoformat(),
            "end": (today + timedelta(days=1)).replace(hour=9, minute=30).isoformat(),
            "location": "Virtual",
            "description": "Daily 7-Specialist Council synchronization",
            "calendar": "Demo",
            "all_day": False
        },
        {
            "id": "mock-3",
            "title": "Infrastructure Review",
            "start": (today + timedelta(days=3)).replace(hour=14, minute=0).isoformat(),
            "end": (today + timedelta(days=3)).replace(hour=15, minute=0).isoformat(),
            "location": "Cherokee AI Lab",
            "description": "Monthly infrastructure and capacity planning",
            "calendar": "Demo",
            "all_day": False
        }
    ]


def get_events_for_day(year: int, month: int, day: int) -> List[Dict]:
    """Get events for a specific day"""
    events = get_events(year, month)
    target_date = datetime(year, month, day).date()

    day_events = []
    for event in events:
        try:
            event_start = datetime.fromisoformat(event["start"].replace("Z", "+00:00"))
            if event_start.date() == target_date:
                day_events.append(event)
        except:
            pass

    return day_events


def sync_calendars() -> Dict:
    """Force sync with iCloud (clear cache)"""
    if REDIS_AVAILABLE:
        # Clear all cached events
        keys = redis_client.keys("sag:calendar:events:*")
        if keys:
            redis_client.delete(*keys)

    # Verify connection
    client = connect_to_icloud()
    if client:
        return {"status": "synced", "message": "Calendar cache cleared and reconnected"}
    else:
        return {"status": "error", "message": "iCloud not configured or connection failed"}
```

---

### Task 2: Add Calendar API Endpoints

Location: `/home/dereadi/sag_unified_interface/app.py`

Add these imports and endpoints:

```python
# Add import at top
from calendar_sync import (
    get_events, get_events_for_day, get_calendars,
    sync_calendars, get_icloud_config, set_icloud_config
)

# CALENDAR API ENDPOINTS

@app.route("/api/calendar/events")
def api_calendar_events():
    """Get calendar events for a month"""
    year = request.args.get("year", datetime.now().year, type=int)
    month = request.args.get("month", datetime.now().month, type=int)
    calendar_id = request.args.get("calendar_id")

    events = get_events(year, month, calendar_id)
    return jsonify({"events": events, "year": year, "month": month})


@app.route("/api/calendar/events/<int:year>/<int:month>/<int:day>")
def api_calendar_day_events(year, month, day):
    """Get events for a specific day"""
    events = get_events_for_day(year, month, day)
    return jsonify({"events": events, "date": f"{year}-{month:02d}-{day:02d}"})


@app.route("/api/calendar/calendars")
def api_calendar_list():
    """Get list of available calendars"""
    calendars = get_calendars()
    return jsonify({"calendars": calendars})


@app.route("/api/calendar/sync", methods=["POST"])
def api_calendar_sync():
    """Force calendar sync"""
    result = sync_calendars()
    return jsonify(result)


@app.route("/api/calendar/config", methods=["GET", "POST"])
def api_calendar_config():
    """Get or set iCloud configuration"""
    if request.method == "GET":
        config = get_icloud_config()
        if config:
            # Don't expose password
            return jsonify({
                "configured": True,
                "apple_id": config.get("apple_id", ""),
                "has_password": bool(config.get("app_password"))
            })
        return jsonify({"configured": False})

    elif request.method == "POST":
        data = request.json
        if not data.get("apple_id") or not data.get("app_password"):
            return jsonify({"error": "apple_id and app_password required"}), 400

        success = set_icloud_config({
            "apple_id": data["apple_id"],
            "app_password": data["app_password"]
        })

        if success:
            # Test connection
            from calendar_sync import connect_to_icloud
            client = connect_to_icloud()
            if client:
                return jsonify({"status": "connected", "message": "iCloud calendar connected"})
            else:
                return jsonify({"status": "error", "message": "Credentials saved but connection failed"})

        return jsonify({"error": "Failed to save configuration"}), 500
```

---

### Task 3: Add Calendar CSS Styling

Location: `/home/dereadi/sag_unified_interface/static/css/unified.css`

```css
/* ========================================
   CALENDAR VIEW STYLES
   ======================================== */

.calendar-container {
    display: grid;
    grid-template-columns: 3fr 1fr;
    gap: 20px;
    padding: 20px;
}

.calendar-main {
    background: var(--card-bg, #1a1a2e);
    border-radius: 12px;
    padding: 20px;
}

.calendar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.calendar-header h3 {
    margin: 0;
    font-size: 1.5rem;
    color: var(--text-primary, #fff);
}

.cal-nav {
    background: var(--button-bg, #2d2d44);
    border: none;
    color: var(--text-primary, #fff);
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 1rem;
    transition: background 0.2s;
}

.cal-nav:hover {
    background: var(--button-hover, #3d3d54);
}

#cal-month-year {
    font-size: 1.3rem;
    font-weight: 600;
    color: var(--text-primary, #fff);
}

.calendar-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 2px;
}

.cal-day-header {
    text-align: center;
    padding: 10px;
    font-weight: 600;
    color: var(--text-secondary, #888);
    font-size: 0.85rem;
    text-transform: uppercase;
}

.cal-day {
    aspect-ratio: 1;
    min-height: 80px;
    background: var(--card-bg-light, #252540);
    border-radius: 6px;
    padding: 8px;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
}

.cal-day:hover {
    background: var(--card-bg-hover, #2d2d50);
    transform: translateY(-2px);
}

.cal-day.other-month {
    opacity: 0.4;
}

.cal-day.today {
    background: var(--accent-color, #4a9eff);
    color: #fff;
}

.cal-day.selected {
    outline: 2px solid var(--accent-color, #4a9eff);
    outline-offset: 2px;
}

.cal-day-number {
    font-weight: 600;
    font-size: 0.95rem;
}

.cal-day-events {
    display: flex;
    flex-wrap: wrap;
    gap: 2px;
    margin-top: 4px;
}

.event-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent-color, #4a9eff);
}

.event-dot.work { background: #4a9eff; }
.event-dot.personal { background: #50fa7b; }
.event-dot.meeting { background: #ff79c6; }

/* Event sidebar */
.calendar-events {
    background: var(--card-bg, #1a1a2e);
    border-radius: 12px;
    padding: 20px;
    max-height: 600px;
    overflow-y: auto;
}

.calendar-events h3 {
    margin: 0 0 15px 0;
    color: var(--text-primary, #fff);
    font-size: 1.1rem;
    border-bottom: 1px solid var(--border-color, #333);
    padding-bottom: 10px;
}

#events-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.event-item {
    background: var(--card-bg-light, #252540);
    border-radius: 8px;
    padding: 12px;
    border-left: 3px solid var(--accent-color, #4a9eff);
    cursor: pointer;
    transition: all 0.2s;
}

.event-item:hover {
    background: var(--card-bg-hover, #2d2d50);
    transform: translateX(4px);
}

.event-time {
    font-size: 0.8rem;
    color: var(--accent-color, #4a9eff);
    margin-bottom: 4px;
}

.event-title {
    font-weight: 600;
    color: var(--text-primary, #fff);
    margin-bottom: 4px;
}

.event-location {
    font-size: 0.85rem;
    color: var(--text-secondary, #888);
}

.event-calendar-name {
    font-size: 0.75rem;
    color: var(--text-muted, #666);
    margin-top: 4px;
}

/* Event detail modal */
.event-detail-modal {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: var(--card-bg, #1a1a2e);
    border-radius: 12px;
    padding: 24px;
    width: 90%;
    max-width: 500px;
    z-index: 1001;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.event-detail-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 20px;
}

.event-detail-title {
    font-size: 1.3rem;
    font-weight: 600;
    color: var(--text-primary, #fff);
}

.event-detail-close {
    background: none;
    border: none;
    color: var(--text-secondary, #888);
    font-size: 1.5rem;
    cursor: pointer;
    line-height: 1;
}

.event-detail-row {
    display: flex;
    gap: 12px;
    margin-bottom: 12px;
    color: var(--text-primary, #fff);
}

.event-detail-label {
    color: var(--text-secondary, #888);
    min-width: 80px;
}

.event-detail-value {
    flex: 1;
}

/* Calendar config in settings */
.calendar-config-section {
    background: var(--card-bg-light, #252540);
    border-radius: 8px;
    padding: 16px;
    margin-top: 10px;
}

.calendar-config-status {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
}

.calendar-config-status.connected {
    color: #50fa7b;
}

.calendar-config-status.disconnected {
    color: #ff5555;
}

/* Sync button */
.sync-button {
    background: var(--button-bg, #2d2d44);
    border: none;
    color: var(--text-primary, #fff);
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.9rem;
}

.sync-button:hover {
    background: var(--button-hover, #3d3d54);
}

.sync-button.syncing {
    opacity: 0.7;
    pointer-events: none;
}

/* No events message */
.no-events {
    text-align: center;
    padding: 30px;
    color: var(--text-secondary, #888);
}

.no-events-icon {
    font-size: 2rem;
    margin-bottom: 10px;
    opacity: 0.5;
}

/* Mobile responsive */
@media (max-width: 900px) {
    .calendar-container {
        grid-template-columns: 1fr;
    }

    .cal-day {
        min-height: 60px;
    }

    .cal-day-header {
        font-size: 0.75rem;
    }
}
```

---

### Task 4: Update Calendar JavaScript

The existing JavaScript needs enhancement. Replace/update in control-room.js:

```javascript
// ========================================
// CALENDAR VIEW
// ========================================

var calendarState = {
    currentDate: new Date(),
    selectedDate: null,
    events: [],
    calendars: []
};

function loadCalendarView() {
    // Check if iCloud configured
    checkCalendarConfig();

    // Render calendar grid
    renderCalendar();

    // Load events
    loadCalendarEvents();

    // Set up navigation
    var prevBtn = document.getElementById("cal-prev");
    var nextBtn = document.getElementById("cal-next");

    if (prevBtn) {
        prevBtn.onclick = function() {
            calendarState.currentDate.setMonth(calendarState.currentDate.getMonth() - 1);
            renderCalendar();
            loadCalendarEvents();
        };
    }

    if (nextBtn) {
        nextBtn.onclick = function() {
            calendarState.currentDate.setMonth(calendarState.currentDate.getMonth() + 1);
            renderCalendar();
            loadCalendarEvents();
        };
    }
}

function checkCalendarConfig() {
    fetch("/api/calendar/config")
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (!data.configured) {
                showCalendarSetupPrompt();
            }
        })
        .catch(function(err) {
            console.log("Calendar config check failed:", err);
        });
}

function showCalendarSetupPrompt() {
    var eventsList = document.getElementById("events-list");
    if (eventsList) {
        eventsList.innerHTML =
            '<div class="no-events">' +
            '<div class="no-events-icon">📅</div>' +
            '<p>Connect your iCloud calendar to see your events here.</p>' +
            '<button onclick="openSettingsForCalendar()" class="config-button">Configure in Settings</button>' +
            '</div>';
    }
}

function openSettingsForCalendar() {
    switchView("settings");
    // Scroll to calendar section after a brief delay
    setTimeout(function() {
        var calSection = document.querySelector('[data-platform="calendar"]');
        if (calSection) {
            calSection.scrollIntoView({ behavior: "smooth" });
        }
    }, 300);
}

function renderCalendar() {
    var grid = document.getElementById("calendar-grid");
    var monthYear = document.getElementById("cal-month-year");

    if (!grid) return;

    var year = calendarState.currentDate.getFullYear();
    var month = calendarState.currentDate.getMonth();

    // Update header
    var monthNames = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"];
    if (monthYear) {
        monthYear.textContent = monthNames[month] + " " + year;
    }

    // Build calendar grid
    var html = "";

    // Day headers
    var dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    for (var d = 0; d < 7; d++) {
        html += '<div class="cal-day-header">' + dayNames[d] + '</div>';
    }

    // Get first day of month and total days
    var firstDay = new Date(year, month, 1).getDay();
    var daysInMonth = new Date(year, month + 1, 0).getDate();
    var daysInPrevMonth = new Date(year, month, 0).getDate();

    // Today reference
    var today = new Date();
    var isCurrentMonth = (today.getFullYear() === year && today.getMonth() === month);

    // Previous month days
    for (var p = firstDay - 1; p >= 0; p--) {
        var dayNum = daysInPrevMonth - p;
        html += '<div class="cal-day other-month" data-day="' + dayNum + '" data-month="' + (month - 1) + '">' +
                '<span class="cal-day-number">' + dayNum + '</span>' +
                '</div>';
    }

    // Current month days
    for (var i = 1; i <= daysInMonth; i++) {
        var isToday = (isCurrentMonth && today.getDate() === i);
        var isSelected = (calendarState.selectedDate &&
                          calendarState.selectedDate.getDate() === i &&
                          calendarState.selectedDate.getMonth() === month);

        var classes = "cal-day";
        if (isToday) classes += " today";
        if (isSelected) classes += " selected";

        html += '<div class="' + classes + '" data-day="' + i + '" data-month="' + month + '" data-year="' + year + '" onclick="selectCalendarDay(' + year + ',' + month + ',' + i + ')">' +
                '<span class="cal-day-number">' + i + '</span>' +
                '<div class="cal-day-events" id="events-day-' + i + '"></div>' +
                '</div>';
    }

    // Next month days to fill grid (6 rows x 7 days = 42 cells)
    var totalCells = firstDay + daysInMonth;
    var remaining = (totalCells > 35) ? (42 - totalCells) : (35 - totalCells);

    for (var n = 1; n <= remaining; n++) {
        html += '<div class="cal-day other-month" data-day="' + n + '" data-month="' + (month + 1) + '">' +
                '<span class="cal-day-number">' + n + '</span>' +
                '</div>';
    }

    grid.innerHTML = html;
}

function loadCalendarEvents() {
    var year = calendarState.currentDate.getFullYear();
    var month = calendarState.currentDate.getMonth() + 1; // API expects 1-indexed

    fetch("/api/calendar/events?year=" + year + "&month=" + month)
        .then(function(r) { return r.json(); })
        .then(function(data) {
            calendarState.events = data.events || [];
            renderEventDots();
            renderTodayEvents();
        })
        .catch(function(err) {
            console.error("Failed to load calendar events:", err);
        });
}

function renderEventDots() {
    // Clear existing dots
    var dotContainers = document.querySelectorAll(".cal-day-events");
    dotContainers.forEach(function(c) { c.innerHTML = ""; });

    // Group events by day
    var eventsByDay = {};
    calendarState.events.forEach(function(event) {
        try {
            var date = new Date(event.start);
            var day = date.getDate();
            if (!eventsByDay[day]) eventsByDay[day] = [];
            eventsByDay[day].push(event);
        } catch (e) {}
    });

    // Add dots
    Object.keys(eventsByDay).forEach(function(day) {
        var container = document.getElementById("events-day-" + day);
        if (container) {
            var events = eventsByDay[day];
            // Show up to 3 dots
            for (var i = 0; i < Math.min(events.length, 3); i++) {
                var dot = document.createElement("span");
                dot.className = "event-dot";
                container.appendChild(dot);
            }
            // Show +N indicator for more
            if (events.length > 3) {
                var more = document.createElement("span");
                more.className = "event-more";
                more.textContent = "+" + (events.length - 3);
                container.appendChild(more);
            }
        }
    });
}

function renderTodayEvents() {
    var eventsList = document.getElementById("events-list");
    if (!eventsList) return;

    // Filter events for selected day or today
    var targetDate = calendarState.selectedDate || new Date();
    var dayEvents = calendarState.events.filter(function(event) {
        try {
            var eventDate = new Date(event.start);
            return eventDate.toDateString() === targetDate.toDateString();
        } catch (e) {
            return false;
        }
    });

    if (dayEvents.length === 0) {
        eventsList.innerHTML =
            '<div class="no-events">' +
            '<div class="no-events-icon">📭</div>' +
            '<p>No events scheduled</p>' +
            '</div>';
        return;
    }

    var html = "";
    dayEvents.forEach(function(event) {
        var startTime = formatEventTime(event.start);
        var endTime = formatEventTime(event.end);
        var timeStr = event.all_day ? "All day" : (startTime + " - " + endTime);

        html += '<div class="event-item" onclick="showEventDetail(\'' + event.id + '\')">' +
                '<div class="event-time">' + timeStr + '</div>' +
                '<div class="event-title">' + escapeHtml(event.title) + '</div>' +
                (event.location ? '<div class="event-location">📍 ' + escapeHtml(event.location) + '</div>' : '') +
                '<div class="event-calendar-name">' + escapeHtml(event.calendar || 'Calendar') + '</div>' +
                '</div>';
    });

    eventsList.innerHTML = html;
}

function selectCalendarDay(year, month, day) {
    calendarState.selectedDate = new Date(year, month, day);

    // Update visual selection
    document.querySelectorAll(".cal-day.selected").forEach(function(el) {
        el.classList.remove("selected");
    });

    var selected = document.querySelector('.cal-day[data-year="' + year + '"][data-month="' + month + '"][data-day="' + day + '"]');
    if (selected) {
        selected.classList.add("selected");
    }

    // Update events sidebar header
    var eventsHeader = document.querySelector(".calendar-events h3");
    if (eventsHeader) {
        var date = calendarState.selectedDate;
        var options = { weekday: 'long', month: 'short', day: 'numeric' };
        eventsHeader.textContent = date.toLocaleDateString('en-US', options);
    }

    renderTodayEvents();
}

function formatEventTime(isoString) {
    try {
        var date = new Date(isoString);
        return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
    } catch (e) {
        return "";
    }
}

function showEventDetail(eventId) {
    var event = calendarState.events.find(function(e) { return e.id === eventId; });
    if (!event) return;

    var modal = document.createElement("div");
    modal.className = "modal-overlay";
    modal.onclick = function(e) {
        if (e.target === modal) modal.remove();
    };

    var startTime = formatEventTime(event.start);
    var endTime = formatEventTime(event.end);
    var dateStr = new Date(event.start).toLocaleDateString('en-US', {
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    });

    modal.innerHTML =
        '<div class="event-detail-modal">' +
        '<div class="event-detail-header">' +
        '<div class="event-detail-title">' + escapeHtml(event.title) + '</div>' +
        '<button class="event-detail-close" onclick="this.closest(\'.modal-overlay\').remove()">&times;</button>' +
        '</div>' +
        '<div class="event-detail-row">' +
        '<span class="event-detail-label">When:</span>' +
        '<span class="event-detail-value">' + dateStr + '<br>' + (event.all_day ? 'All day' : startTime + ' - ' + endTime) + '</span>' +
        '</div>' +
        (event.location ?
            '<div class="event-detail-row">' +
            '<span class="event-detail-label">Where:</span>' +
            '<span class="event-detail-value">' + escapeHtml(event.location) + '</span>' +
            '</div>' : '') +
        (event.description ?
            '<div class="event-detail-row">' +
            '<span class="event-detail-label">Notes:</span>' +
            '<span class="event-detail-value">' + escapeHtml(event.description) + '</span>' +
            '</div>' : '') +
        '<div class="event-detail-row">' +
        '<span class="event-detail-label">Calendar:</span>' +
        '<span class="event-detail-value">' + escapeHtml(event.calendar || 'Default') + '</span>' +
        '</div>' +
        '</div>';

    document.body.appendChild(modal);
}

function syncCalendar() {
    var syncBtn = document.querySelector(".sync-button");
    if (syncBtn) {
        syncBtn.classList.add("syncing");
        syncBtn.textContent = "Syncing...";
    }

    fetch("/api/calendar/sync", { method: "POST" })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (syncBtn) {
                syncBtn.classList.remove("syncing");
                syncBtn.innerHTML = '🔄 Sync';
            }
            loadCalendarEvents();
        })
        .catch(function(err) {
            console.error("Calendar sync failed:", err);
            if (syncBtn) {
                syncBtn.classList.remove("syncing");
                syncBtn.innerHTML = '🔄 Sync';
            }
        });
}

function escapeHtml(text) {
    if (!text) return "";
    var div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}
```

---

### Task 5: Add Calendar Configuration to Settings

Add to the Settings view HTML (in index.html within `#settings-view`):

```html
<!-- Calendar Configuration -->
<div class="settings-section">
    <h3>Calendar</h3>
    <p class="settings-description">Connect your iCloud calendar to see events in SAG</p>

    <div class="platform-config" data-platform="calendar">
        <div class="platform-header">
            <span class="platform-icon">📅</span>
            <span class="platform-name">iCloud Calendar</span>
            <span class="platform-status" id="calendar-status">Not connected</span>
        </div>
        <button class="config-button" onclick="openCalendarConfigModal()">Configure</button>
    </div>
</div>
```

Add JavaScript for calendar config modal:

```javascript
function openCalendarConfigModal() {
    // Check current config
    fetch("/api/calendar/config")
        .then(function(r) { return r.json(); })
        .then(function(config) {
            showCalendarConfigModal(config);
        });
}

function showCalendarConfigModal(currentConfig) {
    var modal = document.createElement("div");
    modal.className = "modal-overlay";
    modal.onclick = function(e) {
        if (e.target === modal) modal.remove();
    };

    modal.innerHTML =
        '<div class="config-modal">' +
        '<div class="modal-header">' +
        '<h3>iCloud Calendar Configuration</h3>' +
        '<button class="modal-close" onclick="this.closest(\'.modal-overlay\').remove()">&times;</button>' +
        '</div>' +
        '<div class="modal-body">' +
        '<div class="form-group">' +
        '<label>Apple ID (email)</label>' +
        '<input type="email" id="icloud-apple-id" placeholder="your@icloud.com" value="' + (currentConfig.apple_id || '') + '">' +
        '</div>' +
        '<div class="form-group">' +
        '<label>App-Specific Password</label>' +
        '<input type="password" id="icloud-app-password" placeholder="xxxx-xxxx-xxxx-xxxx">' +
        '<small>Generate at <a href="https://appleid.apple.com/account/manage" target="_blank">appleid.apple.com</a> → Sign-In and Security → App-Specific Passwords</small>' +
        '</div>' +
        '</div>' +
        '<div class="modal-footer">' +
        '<button class="btn-secondary" onclick="this.closest(\'.modal-overlay\').remove()">Cancel</button>' +
        '<button class="btn-primary" onclick="saveCalendarConfig()">Connect</button>' +
        '</div>' +
        '</div>';

    document.body.appendChild(modal);
}

function saveCalendarConfig() {
    var appleId = document.getElementById("icloud-apple-id").value;
    var appPassword = document.getElementById("icloud-app-password").value;

    if (!appleId || !appPassword) {
        alert("Please enter both Apple ID and App-Specific Password");
        return;
    }

    fetch("/api/calendar/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            apple_id: appleId,
            app_password: appPassword
        })
    })
    .then(function(r) { return r.json(); })
    .then(function(result) {
        if (result.status === "connected") {
            document.querySelector(".modal-overlay").remove();
            var status = document.getElementById("calendar-status");
            if (status) {
                status.textContent = "Connected";
                status.className = "platform-status connected";
            }
            // Refresh calendar if viewing
            if (document.getElementById("calendar-view").classList.contains("active")) {
                loadCalendarEvents();
            }
        } else {
            alert("Connection failed: " + (result.message || result.error));
        }
    })
    .catch(function(err) {
        alert("Error saving configuration: " + err);
    });
}
```

---

## Security Considerations

1. **App-Specific Passwords**: Users MUST use app-specific passwords, not their main Apple ID password
2. **Credential Storage**: In production, encrypt credentials before storing in Redis
3. **HTTPS**: iCloud CalDAV requires HTTPS - our connection handles this
4. **Token Rotation**: Consider prompting users to rotate app-specific passwords periodically
5. **Rate Limiting**: iCloud may rate-limit requests - cache aggressively

---

## Dependencies

Install Python packages on redfin:

```bash
pip install caldav icalendar
```

---

## Testing Checklist

- [ ] Calendar view renders correctly
- [ ] Month navigation (prev/next) works
- [ ] Today is highlighted
- [ ] Clicking a day shows that day's events
- [ ] Mock events show when iCloud not configured
- [ ] Settings → Calendar configure modal opens
- [ ] App-specific password saves successfully
- [ ] iCloud connection succeeds with valid credentials
- [ ] Events sync from iCloud calendar
- [ ] Event detail modal shows full info
- [ ] Sync button clears cache and refetches

---

## File Locations

| File | Purpose |
|------|---------|
| `/home/dereadi/sag_unified_interface/calendar_sync.py` | iCloud CalDAV integration module |
| `/home/dereadi/sag_unified_interface/app.py` | Calendar API endpoints |
| `/home/dereadi/sag_unified_interface/static/js/control-room.js` | Calendar UI JavaScript |
| `/home/dereadi/sag_unified_interface/static/css/unified.css` | Calendar styling |
| `/home/dereadi/sag_unified_interface/templates/index.html` | Calendar view HTML |

---

## External Resources

- **iCloud CalDAV**: https://support.apple.com/en-us/102571
- **App-Specific Passwords**: https://support.apple.com/en-us/HT204397
- **caldav Python Library**: https://github.com/python-caldav/caldav
- **icalendar Library**: https://icalendar.readthedocs.io/

---

## Success Criteria

1. ✅ User can view monthly calendar grid
2. ✅ User can navigate between months
3. ✅ Events appear as dots on calendar days
4. ✅ Clicking a day shows events in sidebar
5. ✅ User can configure iCloud credentials in Settings
6. ✅ Events sync from iPhone calendar
7. ✅ Event details viewable in modal

---

*For Seven Generations*
