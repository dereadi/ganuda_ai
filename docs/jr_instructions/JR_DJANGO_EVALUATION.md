# Jr Task: Evaluate Django 6.0 for Cherokee AI Federation

**Task ID:** task-django-eval-001
**Assigned To:** jr-redfin-gecko (won bid: 0.83 composite score)
**Priority:** P2
**Node:** redfin
**Created:** December 21, 2025

---

## Context

Django 6.0 is the latest stable release of the Python web framework. We need to evaluate if it's suitable for building:
1. A unified admin dashboard for the Cherokee AI Federation
2. REST API layer (potentially replacing/augmenting our Flask gateway)
3. Web interface for thermal memory browsing and Council interactions

---

## Current Infrastructure

| Component | Technology | Notes |
|-----------|------------|-------|
| LLM Gateway | Flask + Python | Port 8080 on redfin |
| SAG Interface | Python web app | Port 4000 on redfin |
| Database | PostgreSQL | bluefin (zammad_production) |
| Frontend | Various | Kanban (3001), Grafana (3000) |

---

## Evaluation Criteria

### 1. Admin Dashboard Generation
Django's killer feature is automatic admin interface from models.

**Test:**
```python
# Would our thermal_memory_archive become browsable?
from django.contrib import admin
from .models import ThermalMemory, JrAgentState, CouncilVote

admin.site.register(ThermalMemory)
admin.site.register(JrAgentState)
admin.site.register(CouncilVote)
```

**Questions to answer:**
- Can we generate admin for existing PostgreSQL tables without migration?
- How customizable is the admin interface?
- Can we add Council vote visualizations?

### 2. REST API Capabilities
Django REST Framework (DRF) is mature and well-documented.

**Compare with current Flask gateway:**
- Authentication (we use API keys)
- Rate limiting
- Request/response serialization
- OpenAPI/Swagger generation

**Compatibility check:**
- Can DRF serve `/v1/chat/completions` OpenAI-compatible endpoint?
- Can we keep Flask for LLM routing and add Django for admin?

### 3. PostgreSQL Integration
Django ORM vs raw psycopg2.

**Test:**
- Connect to existing zammad_production database
- Map existing tables (thermal_memory_archive, jr_agent_state, etc.)
- Query performance comparison

### 4. Deployment on 6-Node Infrastructure
**Questions:**
- Gunicorn/uWSGI deployment alongside existing services?
- Static file serving (whitenoise vs nginx)?
- Session management across nodes?

---

## Proof of Concept Tasks

### POC 1: Thermal Memory Browser
Create Django app that:
1. Connects to zammad_production
2. Lists thermal memories with search/filter
3. Shows memory relationships graph
4. Displays temperature scores with color coding

### POC 2: Council Vote Dashboard
Create view showing:
1. Recent Council votes
2. Specialist voting patterns
3. Dissent detection visualization
4. Vote audit trail

### POC 3: Jr Agent Monitor
Display:
1. Active Jr agents across nodes
2. Task bidding activity
3. Episodic memory timeline
4. Success rate trends

---

## Decision Framework

**Proceed with Django if:**
- Admin generation saves significant development time
- PostgreSQL integration works with existing tables
- Can coexist with Flask gateway
- Deployment complexity is manageable

**Stay with Flask if:**
- Django admin customization is too limiting
- ORM adds too much overhead for our queries
- Deployment conflicts with existing services
- Team learning curve too steep

**Hybrid approach:**
- Django for admin/dashboards (port 4001?)
- Flask for LLM gateway (port 8080)
- Shared PostgreSQL backend

---

## Deliverables

1. POC Django app with thermal memory browser
2. Performance comparison report
3. Deployment guide for redfin
4. Recommendation with Council vote

---

## Resources

- Django 6.0 docs: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- Existing Flask gateway: `/ganuda/services/llm_gateway/gateway.py`
- Database config: See `DB_CONFIG` in any `/ganuda/lib/*.py`

---

*For Seven Generations - Cherokee AI Federation*
