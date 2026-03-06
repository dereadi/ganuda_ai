# Jr Instruction: VetAssist Feedback Widget + Thermal Bridge

**Task ID:** VA-FEEDBACK
**Kanban:** #1852
**Priority:** 3
**Assigned:** Software Engineer Jr.

---

## Overview

Create a feedback endpoint for VetAssist that bridges user feedback to thermal memory for low ratings.

---

## Step 1: Create the feedback blueprint

Create `/ganuda/services/vetassist/feedback_widget.py`

```python
"""VetAssist Feedback Widget: Collects user ratings, bridges to thermal memory."""

from datetime import datetime
from flask import Blueprint, request, jsonify
import psycopg2

feedback_bp = Blueprint("feedback", __name__)

THERMAL_DB = {
    "host": "192.168.132.222",
    "user": "claude",
    "dbname": "zammad_production"
}

@feedback_bp.route("/api/feedback", methods=["POST"])
def submit_feedback():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400
    rating = data.get("rating")
    comment = data.get("comment", "")[:1000]
    page = data.get("page", "unknown")
    session_id = data.get("session_id", "")
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"error": "rating must be 1-5"}), 400
    if rating <= 2:
        _bridge_to_thermal(rating, comment, page)
    return jsonify({"status": "received", "rating": rating}), 201

def _bridge_to_thermal(rating, comment, page):
    try:
        conn = psycopg2.connect(**THERMAL_DB)
        cur = conn.cursor()
        content = (
            f"VETASSIST USER FEEDBACK ALERT (rating={rating}/5)\n"
            f"Page: {page}\n"
            f"Comment: {comment[:500]}\n"
            f"Time: {datetime.now().isoformat()}"
        )
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (original_content, temperature_score, sacred_pattern, memory_hash)
            VALUES (%s, 80, false, encode(sha256((%s || now()::text)::bytea), 'hex'))
        """, (content, f"vetassist-feedback-{rating}-"))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Thermal bridge error: {e}")
```

---

## Verification

```text
python3 -c "
from feedback_widget import feedback_bp
from flask import Flask
app = Flask(__name__)
app.register_blueprint(feedback_bp)
with app.test_client() as c:
    r = c.post('/api/feedback', json={'rating': 2, 'comment': 'Test', 'page': '/claims'})
    print(r.status_code, r.get_json())
"
```
