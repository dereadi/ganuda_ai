# Jr Task: Build Council Vote Dashboard in Django

**Task ID:** task-council-dashboard-001
**Priority:** P2
**Node:** redfin
**Created:** December 21, 2025
**Requested By:** TPM

---

## Context

Django 6.0 is now running at http://192.168.132.223:4001/ with thermal memory API working. We need a visual dashboard showing Council votes, specialist activity, and decision history.

---

## Prerequisites

- Django running on port 4001 (verified)
- API endpoints working:
  - `/api/thermal/hot` - Hot memories
  - `/api/thermal/search?q=<query>` - Search memories
  - `/api/tribe` - Tribe status

---

## Required Dashboard Views

### 1. Council Vote History

**URL:** `/dashboard/council/`

**Features:**
- List of recent Council votes
- For each vote show:
  - Decision hash (short)
  - Prompt snippet (first 100 chars)
  - Confidence score with color (green >=80%, yellow 60-79%, red <60%)
  - Voting date/time
  - Link to full vote details

```python
# thermal_browser/views.py

from django.shortcuts import render
from django.db import connection

def council_history(request):
    """List recent Council votes"""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT decision_hash, LEFT(prompt, 100) as prompt_snippet,
                   confidence, response_time_ms, created_at
            FROM council_votes
            ORDER BY created_at DESC
            LIMIT 50
        """)
        columns = [col[0] for col in cur.description]
        votes = [dict(zip(columns, row)) for row in cur.fetchall()]

    return render(request, 'thermal_browser/council_history.html', {
        'votes': votes
    })
```

### 2. Vote Detail View

**URL:** `/dashboard/council/<decision_hash>/`

**Features:**
- Full prompt
- Full response
- Individual specialist votes from `council_reasoning_log`:
  - Specialist name
  - Position (support/oppose/abstain)
  - Confidence score
  - Reasoning
  - Concern flags

```python
def vote_detail(request, decision_hash):
    """Show single vote with all specialist reasoning"""
    with connection.cursor() as cur:
        # Get main vote
        cur.execute("""
            SELECT * FROM council_votes WHERE decision_hash = %s
        """, [decision_hash])
        vote = dict(zip([c[0] for c in cur.description], cur.fetchone()))

        # Get specialist votes
        cur.execute("""
            SELECT specialist, position, confidence, reasoning, concern_flags
            FROM council_reasoning_log
            WHERE vote_id = %s
            ORDER BY specialist
        """, [vote['id']])
        specialists = [dict(zip([c[0] for c in cur.description], row))
                       for row in cur.fetchall()]

    return render(request, 'thermal_browser/vote_detail.html', {
        'vote': vote,
        'specialists': specialists
    })
```

### 3. Specialist Activity Chart

**URL:** `/dashboard/specialists/`

**Features:**
- Chart showing each specialist's voting patterns
- Support vs oppose ratio
- Concern flag frequency
- Average confidence by specialist

```python
def specialist_stats(request):
    """Specialist voting patterns"""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT specialist,
                   COUNT(*) as total_votes,
                   COUNT(*) FILTER (WHERE position = 'support') as supports,
                   COUNT(*) FILTER (WHERE position = 'oppose') as opposes,
                   AVG(confidence) as avg_confidence,
                   COUNT(*) FILTER (WHERE concern_flags IS NOT NULL AND concern_flags != '[]') as concerns_raised
            FROM council_reasoning_log
            GROUP BY specialist
            ORDER BY specialist
        """)
        columns = [col[0] for col in cur.description]
        specialists = [dict(zip(columns, row)) for row in cur.fetchall()]

    return render(request, 'thermal_browser/specialist_stats.html', {
        'specialists': specialists
    })
```

---

## Template Examples

### Base Template

Create `/ganuda/cherokee_admin/thermal_browser/templates/thermal_browser/base.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}Cherokee AI Council{% endblock %}</title>
    <style>
        body { font-family: system-ui, sans-serif; margin: 0; padding: 20px; }
        nav { background: #2c3e50; padding: 10px 20px; margin: -20px -20px 20px -20px; }
        nav a { color: white; margin-right: 20px; text-decoration: none; }
        nav a:hover { text-decoration: underline; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #ddd; }
        tr:hover { background: #f5f5f5; }
        .confidence-high { color: #27ae60; font-weight: bold; }
        .confidence-med { color: #f39c12; }
        .confidence-low { color: #e74c3c; }
        .concern-flag { background: #ffe5e5; padding: 2px 6px; border-radius: 4px; margin: 2px; display: inline-block; }
    </style>
</head>
<body>
    <nav>
        <a href="/dashboard/council/">Council Votes</a>
        <a href="/dashboard/specialists/">Specialists</a>
        <a href="/admin/">Admin</a>
        <a href="/api/thermal/hot">API: Hot Memories</a>
    </nav>
    {% block content %}{% endblock %}
</body>
</html>
```

### Council History Template

Create `/ganuda/cherokee_admin/thermal_browser/templates/thermal_browser/council_history.html`:

```html
{% extends 'thermal_browser/base.html' %}
{% block title %}Council Vote History{% endblock %}
{% block content %}
<h1>Council Vote History</h1>
<table>
    <thead>
        <tr>
            <th>Date</th>
            <th>Prompt</th>
            <th>Confidence</th>
            <th>Response Time</th>
            <th>Details</th>
        </tr>
    </thead>
    <tbody>
    {% for vote in votes %}
        <tr>
            <td>{{ vote.created_at|date:"M d, H:i" }}</td>
            <td>{{ vote.prompt_snippet }}...</td>
            <td class="{% if vote.confidence >= 80 %}confidence-high{% elif vote.confidence >= 60 %}confidence-med{% else %}confidence-low{% endif %}">
                {{ vote.confidence|floatformat:1 }}%
            </td>
            <td>{{ vote.response_time_ms|floatformat:0 }}ms</td>
            <td><a href="/dashboard/council/{{ vote.decision_hash }}/">View</a></td>
        </tr>
    {% empty %}
        <tr><td colspan="5">No council votes yet.</td></tr>
    {% endfor %}
    </tbody>
</table>
{% endblock %}
```

---

## URL Configuration

Update `/ganuda/cherokee_admin/thermal_browser/urls.py`:

```python
from django.urls import path
from . import views, api

urlpatterns = [
    # API endpoints
    path('api/thermal/hot', api.hot_memories),
    path('api/thermal/search', api.search_memories),
    path('api/thermal/explain', api.thermal_explain),
    path('api/tribe', api.tribe_status),

    # Dashboard views
    path('dashboard/council/', views.council_history, name='council_history'),
    path('dashboard/council/<str:decision_hash>/', views.vote_detail, name='vote_detail'),
    path('dashboard/specialists/', views.specialist_stats, name='specialist_stats'),
]
```

---

## Database Tables Used

| Table | Purpose |
|-------|---------|
| council_votes | Main vote records |
| council_reasoning_log | Individual specialist votes |
| thermal_memory_archive | Memories (for cross-reference) |

---

## Testing

1. After creating views and templates:
   ```bash
   curl http://192.168.132.223:4001/dashboard/council/
   ```

2. Check for errors:
   ```bash
   tail -20 /ganuda/logs/django.log
   ```

---

## Success Criteria

1. `/dashboard/council/` shows vote history
2. Clicking a vote shows specialist breakdown
3. `/dashboard/specialists/` shows voting patterns
4. No Python errors in Django log

---

*For Seven Generations - Cherokee AI Federation*
