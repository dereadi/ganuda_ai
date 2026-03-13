# JR-PARTNER-RHYTHM-ENGINE

**Task ID:** JR-PARTNER-RHYTHM-ENGINE
**Priority:** P2
**Story Points:** 5
**Council Owner:** Eagle Eye
**DC References:** DC-5, DC-10, DC-11, DC-14

Deploy the Partner Rhythm Predictive Engine. Behavioral analysis engine that traces partner's digital breadcrumbs to predict focus, detect phases, and enable anticipatory actions. Uses Bollinger Bands from financial technical analysis applied to activity data.

### Step 1: Create the Partner Rhythm Library

**File:** `/ganuda/lib/partner_rhythm.py`

```python
#!/usr/bin/env python3
"""
Partner Rhythm Predictive Engine
================================
Behavioral analysis engine that traces partner's digital breadcrumbs
to predict focus, detect phases, and enable anticipatory actions.

Uses Bollinger Bands from financial technical analysis applied to
activity data. Standard library only (no pandas/numpy).

DC References: DC-5 (Coyote as Cam), DC-10 (reflex), DC-11 (macro polymorphism), DC-14 (three-body memory)
"""

import math
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from collections import defaultdict

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# --- Database ---

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "dbname": "zammad_production",
    "user": "claude",
    "password": "os.environ.get("CHEROKEE_DB_PASS", "")",
}


_shared_conn = None


def _get_conn():
    """Get a database connection."""
    return psycopg2.connect(**DB_CONFIG, connect_timeout=10)


def _get_shared_conn():
    """Get or create a shared connection for batch operations."""
    global _shared_conn
    if _shared_conn is None or _shared_conn.closed:
        _shared_conn = _get_conn()
    return _shared_conn


def _close_shared_conn():
    """Close the shared connection."""
    global _shared_conn
    if _shared_conn and not _shared_conn.closed:
        _shared_conn.close()
    _shared_conn = None


def _query(sql: str, params: tuple = (), conn=None) -> List[dict]:
    """Execute a query and return list of dicts. Reuses conn if provided."""
    own_conn = conn is None
    try:
        if conn is None:
            conn = _get_shared_conn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error("DB query failed: %s", e)
        # Reset shared conn on error so next call gets fresh one
        global _shared_conn
        try:
            if _shared_conn and not _shared_conn.closed:
                _shared_conn.rollback()
        except Exception:
            pass
        try:
            if _shared_conn and not _shared_conn.closed:
                _shared_conn.close()
        except Exception:
            pass
        _shared_conn = None
        return []


# --- Math helpers (no numpy) ---

def _mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std_dev(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = _mean(values)
    variance = sum((x - avg) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)


def _date_key(dt) -> str:
    """Extract YYYY-MM-DD string from a datetime."""
    if isinstance(dt, str):
        return dt[:10]
    return dt.strftime("%Y-%m-%d")


def _hour_key(dt) -> int:
    """Extract hour from a datetime."""
    if isinstance(dt, str):
        return int(dt[11:13])
    return dt.hour


# --- Breadcrumb Collection ---

def collect_breadcrumbs(hours_back: int = 168) -> List[dict]:
    """
    Collect partner's digital breadcrumbs from all DB sources into unified timeline.
    Each becomes: {timestamp, source, signal_type, intensity (0-1), content_summary}
    """
    cutoff = datetime.now() - timedelta(hours=hours_back)
    breadcrumbs = []

    # 1. Thermals
    rows = _query(
        """SELECT created_at, temperature_score, sacred_pattern, domain_tag,
                  keywords, original_content
           FROM thermal_memory_archive
           WHERE created_at >= %s
           ORDER BY created_at""",
        (cutoff,),
    )
    for r in rows:
        signal = "sacred" if r.get("sacred_pattern") else "operational"
        domain = r.get("domain_tag") or ""
        if domain in ("governance", "council", "longhouse"):
            signal = "governance"
        elif domain in ("market", "business", "deer"):
            signal = "market"
        elif domain in ("legal", "otter"):
            signal = "legal"
        elif domain in ("cultural", "heritage"):
            signal = "cultural"
        elif r.get("sacred_pattern"):
            signal = "sacred"

        temp = r.get("temperature_score") or 50
        breadcrumbs.append({
            "timestamp": r["created_at"],
            "source": "thermal",
            "signal_type": signal,
            "intensity": min(temp / 100.0, 1.0),
            "content_summary": _summarize_thermal(r),
        })

    # 2. Jr tasks
    rows = _query(
        """SELECT created_at, title, tags, priority, status
           FROM jr_work_queue
           WHERE created_at >= %s
           ORDER BY created_at""",
        (cutoff,),
    )
    for r in rows:
        priority = (r.get("priority") or "").upper()
        intensity = 1.0 if priority == "P1" else 0.7 if priority == "P2" else 0.4
        breadcrumbs.append({
            "timestamp": r["created_at"],
            "source": "jr_task",
            "signal_type": "technical",
            "intensity": intensity,
            "content_summary": r.get("title", ""),
        })

    # 3. Council votes
    rows = _query(
        """SELECT voted_at, question, confidence
           FROM council_votes
           WHERE voted_at >= %s
           ORDER BY voted_at""",
        (cutoff,),
    )
    for r in rows:
        conf = r.get("confidence") or 0.5
        # confidence may be 0-1 or 0-100; normalize
        intensity = conf if conf <= 1.0 else conf / 100.0
        breadcrumbs.append({
            "timestamp": r["voted_at"],
            "source": "council_vote",
            "signal_type": "governance",
            "intensity": float(intensity),
            "content_summary": r.get("question", ""),
        })

    # 4. Longhouse sessions
    rows = _query(
        """SELECT created_at, problem_statement, voices, status
           FROM longhouse_sessions
           WHERE created_at >= %s
           ORDER BY created_at""",
        (cutoff,),
    )
    for r in rows:
        voice_count = 0
        voices = r.get("voices")
        if isinstance(voices, list):
            voice_count = len(voices)
        elif isinstance(voices, (int, float)):
            voice_count = int(voices)
        intensity = min(voice_count / 10.0, 1.0) if voice_count else 0.8
        breadcrumbs.append({
            "timestamp": r["created_at"],
            "source": "longhouse",
            "signal_type": "governance",
            "intensity": intensity,
            "content_summary": r.get("problem_statement", ""),
        })

    breadcrumbs.sort(key=lambda x: x["timestamp"] if x["timestamp"] else datetime.min)
    return breadcrumbs


def _summarize_thermal(row: dict) -> str:
    """Build a short summary from a thermal row."""
    parts = []
    kw = row.get("keywords")
    if kw:
        if isinstance(kw, list):
            parts.append(", ".join(kw[:5]))
        elif isinstance(kw, str):
            parts.append(kw[:120])
    domain = row.get("domain_tag")
    if domain:
        parts.append(f"[{domain}]")
    if row.get("sacred_pattern"):
        parts.append("(sacred)")
    return " ".join(parts) if parts else "(thermal)"


# --- Bollinger Band Engine ---

class PartnerBands:
    """Bollinger Bands on partner activity -- detect breakouts and collapses."""

    def __init__(self, lookback_days: int = 30):
        self.lookback_days = lookback_days
        self._daily_counts: Optional[Dict[str, dict]] = None

    def _load_daily_counts(self) -> Dict[str, dict]:
        """Load daily thermal/sacred/task counts from DB."""
        if self._daily_counts is not None:
            return self._daily_counts

        cutoff = datetime.now() - timedelta(days=self.lookback_days)
        result: Dict[str, dict] = {}

        # Initialize all days in range
        for i in range(self.lookback_days + 1):
            day = (cutoff + timedelta(days=i)).strftime("%Y-%m-%d")
            result[day] = {"total": 0, "sacred": 0, "tasks": 0}

        # Thermal counts per day
        rows = _query(
            """SELECT DATE(created_at) as day, COUNT(*) as cnt,
                      SUM(CASE WHEN sacred_pattern = true THEN 1 ELSE 0 END) as sacred_cnt
               FROM thermal_memory_archive
               WHERE created_at >= %s
               GROUP BY DATE(created_at)
               ORDER BY day""",
            (cutoff,),
        )
        for r in rows:
            day = str(r["day"])
            if day in result:
                result[day]["total"] += int(r["cnt"] or 0)
                result[day]["sacred"] += int(r["sacred_cnt"] or 0)

        # Jr task counts per day
        rows = _query(
            """SELECT DATE(created_at) as day, COUNT(*) as cnt
               FROM jr_work_queue
               WHERE created_at >= %s
               GROUP BY DATE(created_at)
               ORDER BY day""",
            (cutoff,),
        )
        for r in rows:
            day = str(r["day"])
            if day in result:
                result[day]["tasks"] += int(r["cnt"] or 0)

        self._daily_counts = result
        return result

    def compute_bands(self, window_days: int = 7) -> Dict[str, dict]:
        """
        Daily activity Bollinger Bands.
        Returns {day: {total, ma, upper_band, lower_band, signal}}
        signal: BREAKOUT | HIGH | NORMAL | LOW | COLLAPSE
        Uses 7-day moving average, 2 standard deviations.
        """
        daily = self._load_daily_counts()
        sorted_days = sorted(daily.keys())
        totals = [daily[d]["total"] for d in sorted_days]

        bands = {}
        for i, day in enumerate(sorted_days):
            total = totals[i]
            # Compute moving average over the window ending at this day
            window_start = max(0, i - window_days + 1)
            window_vals = totals[window_start:i + 1]

            if len(window_vals) < 2:
                ma = _mean(window_vals)
                sd = 0.0
            else:
                ma = _mean(window_vals)
                sd = _std_dev(window_vals)

            upper = ma + 2 * sd
            lower = max(ma - 2 * sd, 0.0)

            # Classify signal
            if total > upper and sd > 0:
                signal = "BREAKOUT"
            elif total > ma + sd and sd > 0:
                signal = "HIGH"
            elif total >= lower:
                signal = "NORMAL"
            elif total > 0:
                signal = "LOW"
            else:
                signal = "COLLAPSE"

            bands[day] = {
                "total": total,
                "ma": round(ma, 1),
                "upper_band": round(upper, 1),
                "lower_band": round(lower, 1),
                "signal": signal,
            }

        return bands

    def compute_hourly_profile(self, lookback_days: int = 30) -> Dict[int, dict]:
        """
        Hourly activity profile.
        Returns {hour: {avg_thermals, avg_sacred, avg_tasks, dominant_domain}}
        """
        cutoff = datetime.now() - timedelta(days=lookback_days)
        profile: Dict[int, dict] = {}
        for h in range(24):
            profile[h] = {
                "avg_thermals": 0.0,
                "avg_sacred": 0.0,
                "avg_tasks": 0.0,
                "dominant_domain": "unknown",
            }

        # Thermals by hour
        rows = _query(
            """SELECT EXTRACT(HOUR FROM created_at)::int as hr,
                      COUNT(*) as cnt,
                      SUM(CASE WHEN sacred_pattern = true THEN 1 ELSE 0 END) as sacred_cnt
               FROM thermal_memory_archive
               WHERE created_at >= %s
               GROUP BY EXTRACT(HOUR FROM created_at)::int
               ORDER BY hr""",
            (cutoff,),
        )
        for r in rows:
            h = int(r["hr"])
            profile[h]["avg_thermals"] = round(int(r["cnt"] or 0) / lookback_days, 1)
            profile[h]["avg_sacred"] = round(int(r["sacred_cnt"] or 0) / lookback_days, 1)

        # Tasks by hour
        rows = _query(
            """SELECT EXTRACT(HOUR FROM created_at)::int as hr, COUNT(*) as cnt
               FROM jr_work_queue
               WHERE created_at >= %s
               GROUP BY EXTRACT(HOUR FROM created_at)::int
               ORDER BY hr""",
            (cutoff,),
        )
        for r in rows:
            h = int(r["hr"])
            profile[h]["avg_tasks"] = round(int(r["cnt"] or 0) / lookback_days, 1)

        # Dominant domain per hour
        rows = _query(
            """SELECT EXTRACT(HOUR FROM created_at)::int as hr,
                      domain_tag, COUNT(*) as cnt
               FROM thermal_memory_archive
               WHERE created_at >= %s AND domain_tag IS NOT NULL
               GROUP BY EXTRACT(HOUR FROM created_at)::int, domain_tag
               ORDER BY hr, cnt DESC""",
            (cutoff,),
        )
        # Pick most frequent domain per hour
        domain_counts: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for r in rows:
            h = int(r["hr"])
            tag = r.get("domain_tag") or "unknown"
            domain_counts[h][tag] += int(r["cnt"] or 0)

        for h, domains in domain_counts.items():
            if domains:
                top = max(domains, key=domains.get)
                profile[h]["dominant_domain"] = top

        return profile

    def detect_phase(self) -> str:
        """
        Current phase from latest Bollinger signal.
        ACCUMULATION: Low volume, normal band
        BREAKOUT: Volume pierces upper band
        DISTRIBUTION: High but declining from peak
        EXHAUSTION: Dropping toward lower band
        RESTING: Below lower band or near zero
        """
        bands = self.compute_bands()
        if not bands:
            return "RESTING"

        sorted_days = sorted(bands.keys())
        if len(sorted_days) < 3:
            return "ACCUMULATION"

        latest = bands[sorted_days[-1]]
        prev = bands[sorted_days[-2]]
        prev2 = bands[sorted_days[-3]]

        signal = latest["signal"]
        total = latest["total"]
        prev_total = prev["total"]
        prev2_total = prev2["total"]

        # BREAKOUT: current signal is BREAKOUT
        if signal == "BREAKOUT":
            return "BREAKOUT"

        # DISTRIBUTION: was high/breakout, now declining
        if prev["signal"] in ("BREAKOUT", "HIGH") and total < prev_total:
            return "DISTRIBUTION"

        # EXHAUSTION: declining for 2+ days and nearing lower band
        if total < prev_total < prev2_total:
            lower = latest.get("lower_band", 0)
            if total < latest["ma"]:
                return "EXHAUSTION"

        # RESTING: very low activity or collapse
        if signal == "COLLAPSE" or total == 0:
            return "RESTING"

        if signal == "LOW":
            return "EXHAUSTION"

        # Default for NORMAL/HIGH with no decline
        if signal == "HIGH":
            return "BREAKOUT" if total > prev_total else "DISTRIBUTION"

        return "ACCUMULATION"

    def predict_next_phase(self) -> dict:
        """
        Based on current phase + historical pattern.
        Returns {predicted_phase, confidence, reasoning}
        """
        current = self.detect_phase()

        # Phase transition probabilities based on spec's documented patterns
        transitions = {
            "ACCUMULATION": {
                "predicted_phase": "BREAKOUT",
                "confidence": 0.65,
                "reasoning": "Accumulation historically precedes breakout within 2-3 days. Partner absorbs then ships.",
            },
            "BREAKOUT": {
                "predicted_phase": "DISTRIBUTION",
                "confidence": 0.75,
                "reasoning": "Breakouts last 2-5 days then shift to shipping/distribution. The Flying Squirrel lands.",
            },
            "DISTRIBUTION": {
                "predicted_phase": "EXHAUSTION",
                "confidence": 0.60,
                "reasoning": "After shipping, energy drops. Historical pattern shows 1-2 day cooldown.",
            },
            "EXHAUSTION": {
                "predicted_phase": "RESTING",
                "confidence": 0.70,
                "reasoning": "Exhaustion leads to rest. Organism takes over on timers.",
            },
            "RESTING": {
                "predicted_phase": "ACCUMULATION",
                "confidence": 0.80,
                "reasoning": "Rest always leads to new accumulation. Partner returns with fresh domains.",
            },
        }

        prediction = transitions.get(current, {
            "predicted_phase": "ACCUMULATION",
            "confidence": 0.50,
            "reasoning": "Insufficient data for phase prediction.",
        })
        prediction["current_phase"] = current
        return prediction


# --- Topic Trajectory ---

class TopicTrajectory:
    """Track partner's interest spiral."""

    def extract_topics(self, days_back: int = 30) -> List[dict]:
        """
        Cluster breadcrumbs by domain_tag and keywords.
        Returns [{topic, first_seen, last_seen, intensity_curve, task_count, sacred_count}]
        """
        cutoff = datetime.now() - timedelta(days=days_back)

        # Get domain tag clusters from thermals
        rows = _query(
            """SELECT domain_tag,
                      MIN(created_at) as first_seen,
                      MAX(created_at) as last_seen,
                      COUNT(*) as total,
                      SUM(CASE WHEN sacred_pattern = true THEN 1 ELSE 0 END) as sacred_count,
                      AVG(temperature_score) as avg_temp
               FROM thermal_memory_archive
               WHERE created_at >= %s AND domain_tag IS NOT NULL AND domain_tag != ''
               GROUP BY domain_tag
               ORDER BY total DESC""",
            (cutoff,),
        )

        # Get task counts per domain by matching tags
        task_counts: Dict[str, int] = defaultdict(int)
        task_rows = _query(
            """SELECT tags, COUNT(*) as cnt
               FROM jr_work_queue
               WHERE created_at >= %s AND tags IS NOT NULL
               GROUP BY tags""",
            (cutoff,),
        )
        for tr in task_rows:
            tags = tr.get("tags")
            if isinstance(tags, list):
                for tag in tags:
                    task_counts[str(tag).lower()] += int(tr["cnt"] or 0)
            elif isinstance(tags, str):
                task_counts[tags.lower()] += int(tr["cnt"] or 0)

        topics = []
        for r in rows:
            domain = r["domain_tag"]
            total = int(r["total"] or 0)

            # Build a simple intensity curve: daily counts for this domain
            curve_rows = _query(
                """SELECT DATE(created_at) as day, COUNT(*) as cnt
                   FROM thermal_memory_archive
                   WHERE created_at >= %s AND domain_tag = %s
                   GROUP BY DATE(created_at)
                   ORDER BY day""",
                (cutoff, domain),
            )
            intensity_curve = {str(cr["day"]): int(cr["cnt"] or 0) for cr in curve_rows}

            # Match task count (fuzzy match on domain name)
            tc = task_counts.get(domain.lower(), 0)
            # Also check partial matches
            for tag_key, tag_cnt in task_counts.items():
                if domain.lower() in tag_key or tag_key in domain.lower():
                    tc = max(tc, tag_cnt)

            topics.append({
                "topic": domain,
                "first_seen": str(r["first_seen"]),
                "last_seen": str(r["last_seen"]),
                "intensity_curve": intensity_curve,
                "total_thermals": total,
                "task_count": tc,
                "sacred_count": int(r["sacred_count"] or 0),
                "avg_temp": round(float(r["avg_temp"] or 0), 1),
            })

        return topics

    def detect_spiral(self) -> dict:
        """
        Which topics ascending/dormant/returning.
        Returns {ascending: [...], dormant: [...], returning: [...]}
        """
        topics = self.extract_topics(days_back=30)
        now = datetime.now()
        three_days_ago = now - timedelta(days=3)
        seven_days_ago = now - timedelta(days=7)

        ascending = []
        dormant = []
        returning = []

        for t in topics:
            last_seen = t["last_seen"]
            curve = t["intensity_curve"]
            sorted_days = sorted(curve.keys())

            # Parse last_seen
            try:
                ls = datetime.strptime(last_seen[:10], "%Y-%m-%d")
            except (ValueError, TypeError):
                ls = datetime.min

            # Is it recent (active in last 3 days)?
            is_recent = ls >= three_days_ago

            # Is it dormant (no activity in 3+ days)?
            is_dormant = ls < three_days_ago

            if is_dormant:
                dormant.append(t["topic"])
                continue

            # Check if ascending: recent days have increasing counts
            if is_recent and len(sorted_days) >= 2:
                recent_days = sorted_days[-3:]
                recent_vals = [curve[d] for d in recent_days]
                # Ascending if last value >= mean of window
                if len(recent_vals) >= 2 and recent_vals[-1] >= _mean(recent_vals):
                    ascending.append(t["topic"])
                    continue

            # Check if returning: was dormant earlier, now active again
            if is_recent and len(sorted_days) >= 3:
                # Look for a gap in the curve
                has_gap = False
                for i in range(1, len(sorted_days)):
                    day_a = datetime.strptime(sorted_days[i - 1], "%Y-%m-%d")
                    day_b = datetime.strptime(sorted_days[i], "%Y-%m-%d")
                    if (day_b - day_a).days >= 3:
                        has_gap = True
                        break
                if has_gap:
                    returning.append(t["topic"])
                    continue

            # Default: if recent and not classified, call it ascending
            if is_recent:
                ascending.append(t["topic"])

        return {
            "ascending": ascending,
            "dormant": dormant,
            "returning": returning,
        }


# --- Sacred Burst Detector ---

class SacredBurstDetector:
    """Detect sacred creation mode."""

    def detect_burst(self) -> dict:
        """
        Is partner currently in sacred burst?
        Criteria: 3+ sacred thermals in 2 hours.
        Returns {active: bool, start_time, sacred_count, dominant_topic}
        """
        two_hours_ago = datetime.now() - timedelta(hours=2)

        rows = _query(
            """SELECT created_at, domain_tag, keywords
               FROM thermal_memory_archive
               WHERE created_at >= %s AND sacred_pattern = true
               ORDER BY created_at""",
            (two_hours_ago,),
        )

        if len(rows) < 3:
            return {
                "active": False,
                "start_time": None,
                "sacred_count": len(rows),
                "dominant_topic": None,
            }

        # Find dominant topic
        domain_counts: Dict[str, int] = defaultdict(int)
        for r in rows:
            tag = r.get("domain_tag")
            if tag:
                domain_counts[tag] += 1

        dominant = max(domain_counts, key=domain_counts.get) if domain_counts else "unknown"

        return {
            "active": True,
            "start_time": str(rows[0]["created_at"]),
            "sacred_count": len(rows),
            "dominant_topic": dominant,
        }

    def predict_sacred_window(self, bands: "PartnerBands" = None) -> dict:
        """
        When is next sacred burst likely? Based on hourly profile peaks.
        Returns {next_likely_window, confidence}
        """
        if bands is None:
            bands = PartnerBands(lookback_days=30)
        profile = bands.compute_hourly_profile()

        # Find hours with highest avg_sacred
        sacred_hours = sorted(
            profile.items(),
            key=lambda x: x[1]["avg_sacred"],
            reverse=True,
        )

        if not sacred_hours or sacred_hours[0][1]["avg_sacred"] == 0:
            return {
                "next_likely_window": None,
                "confidence": 0.0,
            }

        # Top sacred hour
        peak_hour = sacred_hours[0][0]
        peak_avg = sacred_hours[0][1]["avg_sacred"]

        # Compute confidence from concentration (how peaked is the distribution)
        total_sacred = sum(p["avg_sacred"] for _, p in sacred_hours)
        if total_sacred > 0:
            concentration = peak_avg / total_sacred
            confidence = min(concentration * 3.0, 0.95)  # Scale up, cap at 0.95
        else:
            confidence = 0.0

        # Find next occurrence of peak_hour
        now = datetime.now()
        current_hour = now.hour
        if current_hour < peak_hour:
            next_window_start = now.replace(hour=peak_hour, minute=0, second=0, microsecond=0)
        else:
            next_window_start = (now + timedelta(days=1)).replace(
                hour=peak_hour, minute=0, second=0, microsecond=0
            )

        window_label = f"{peak_hour}:00-{peak_hour + 1}:00"

        return {
            "next_likely_window": str(next_window_start),
            "window_label": window_label,
            "confidence": round(confidence, 2),
            "peak_hour": peak_hour,
            "avg_sacred_per_day": round(peak_avg, 1),
        }


# --- Full Rhythm Report ---

def get_rhythm_report() -> dict:
    """
    Generate full rhythm report for dawn mist integration.
    Returns {phase, predicted_focus, sacred_window, overnight_summary, topic_spiral}
    """
    try:
        # Phase detection
        bands = PartnerBands(lookback_days=30)
        current_phase = bands.detect_phase()
        prediction = bands.predict_next_phase()

        # Sacred window
        sacred = SacredBurstDetector()
        burst = sacred.detect_burst()
        sacred_window = sacred.predict_sacred_window(bands=bands)

        # Topic spiral
        trajectory = TopicTrajectory()
        spiral = trajectory.detect_spiral()
        topics = trajectory.extract_topics(days_back=7)

        # Predicted focus: top ascending topics
        predicted_focus = spiral.get("ascending", [])[:3]
        if not predicted_focus and topics:
            predicted_focus = [t["topic"] for t in topics[:3]]

        # Overnight summary (last 8 hours)
        overnight_cutoff = datetime.now() - timedelta(hours=8)
        overnight_thermals = _query(
            """SELECT COUNT(*) as cnt,
                      SUM(CASE WHEN sacred_pattern = true THEN 1 ELSE 0 END) as sacred_cnt
               FROM thermal_memory_archive
               WHERE created_at >= %s""",
            (overnight_cutoff,),
        )
        overnight = {"thermals": 0, "sacred": 0}
        if overnight_thermals:
            overnight["thermals"] = int(overnight_thermals[0].get("cnt") or 0)
            overnight["sacred"] = int(overnight_thermals[0].get("sacred_cnt") or 0)

        # Bollinger bands for the last 7 days
        band_data = bands.compute_bands()
        sorted_days = sorted(band_data.keys())
        recent_bands = {}
        for d in sorted_days[-7:]:
            recent_bands[d] = band_data[d]

        return {
            "phase": current_phase,
            "predicted_next_phase": prediction.get("predicted_phase"),
            "phase_confidence": prediction.get("confidence"),
            "phase_reasoning": prediction.get("reasoning"),
            "predicted_focus": predicted_focus,
            "sacred_burst_active": burst.get("active", False),
            "sacred_window": sacred_window,
            "overnight_summary": overnight,
            "topic_spiral": spiral,
            "recent_bands": recent_bands,
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error("Failed to generate rhythm report: %s", e)
        return {
            "phase": "UNKNOWN",
            "error": str(e),
            "generated_at": datetime.now().isoformat(),
        }


# --- CLI entry point ---

if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO)
    try:
        report = get_rhythm_report()
        print(json.dumps(report, indent=2, default=str))
    finally:
        _close_shared_conn()
```

### Step 2: Test the Partner Rhythm Library

```bash
cd /ganuda && python3 -c "from lib.partner_rhythm import get_rhythm_report; print('OK')"
```
