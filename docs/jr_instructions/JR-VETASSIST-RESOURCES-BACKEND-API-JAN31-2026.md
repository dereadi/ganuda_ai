# JR Instruction: VetAssist Resources Backend API — Sections, KB Fields, and External Links Endpoints

**Task ID:** VETASSIST-RESOURCES-API-001
**Date:** January 31, 2026
**Priority:** P1
**Type:** backend
**Assigned To:** Software Engineer Jr.
**Depends On:** VETASSIST-RESOURCES-SCHEMA-001 (already completed — DB columns exist)
**Estimated Steps:** 4

---

## Objective

Expose the new KB publishing fields (section, author, status, content_version, source_references) through the existing content API, add a section-grouped endpoint, and create a new endpoint for curated external resource links. This unlocks the frontend's ability to render topic-based sections with integrated official VA links.

---

## Background

Phase 1 (VETASSIST-RESOURCES-SCHEMA-001) added 12 new columns to `educational_content` and created the `vetassist_resource_links` table on bluefin. Phase 2 (VETASSIST-ARTICLES-EXPAND-001) expanded all 17 articles to full-length KB content with section assignments. The database is ready; the API just needs to surface these fields.

Current state:
- `to_dict()` in the content model returns 14 fields; the 12 new columns are NOT exposed
- The content API supports filtering by `tag` and `difficulty` but NOT by `section`
- No endpoint exists for the `vetassist_resource_links` table
- The `__init__.py` API router needs a new import for the resource-links module

---

## Steps

### Step 1: Update EducationalContent model to expose KB fields

**File:** `/ganuda/vetassist/backend/app/models/content.py`

The SQLAlchemy model currently defines columns only through the original 14 fields. The database already has the new columns (from the ALTER TABLE migration), but the model doesn't know about them. Add the column definitions and update `to_dict()`.

**SEARCH/REPLACE in `/ganuda/vetassist/backend/app/models/content.py`:**

Find the existing column definitions section (after `is_published = Column(Boolean, default=True)`) and add the new columns. The exact search pattern depends on the file content, but the new columns should be:

```python
    # KB Publishing Pipeline fields (Phase 1 migration)
    author = Column(String(100), default='Ganuda AI')
    reviewer = Column(String(100))
    reviewed_at = Column(DateTime(timezone=True))
    review_notes = Column(Text)
    review_audit_hash = Column(String(32))
    content_version = Column(Integer, default=1)
    status = Column(String(20), default='published')
    section = Column(String(50))
    section_order = Column(Integer, default=0)
    source_references = Column(Text)
    last_accuracy_check = Column(DateTime(timezone=True))
    needs_update = Column(Boolean, default=False)
```

Then update the `to_dict()` method to include the new fields. Add these entries to the returned dictionary:

```python
            "author": self.author or 'Ganuda AI',
            "content_version": self.content_version or 1,
            "status": self.status or 'published',
            "section": self.section,
            "section_order": self.section_order or 0,
            "source_references": self.source_references,
```

**Do NOT include** `reviewer`, `reviewed_at`, `review_notes`, `review_audit_hash`, `last_accuracy_check`, or `needs_update` in the API response — these are internal editorial fields.

**Verify:** After this change, the API response for any article should include `section`, `section_order`, `author`, `status`, `content_version`, and `source_references` as new fields.

### Step 2: Add section filtering and sections endpoint to content API

**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/content.py`

**2A. Add `section` query parameter to the list endpoint.**

Find the `list_content()` function and add a `section: Optional[str] = None` parameter. Then add a filter:

```python
if section:
    query = query.filter(EducationalContent.section == section)
```

Also add ordering by `section_order` when a section filter is applied:

```python
if section:
    query = query.order_by(EducationalContent.section_order)
```

**2B. Add a new `/sections` endpoint** that returns articles grouped by section.

Add this endpoint BEFORE the `/{content_id}` path route (to avoid the path parameter catching "sections" as an ID):

```python
@router.get("/sections")
async def list_sections(db: Session = Depends(get_db)):
    """Return articles grouped by section with section metadata."""
    section_definitions = {
        "getting-started": {"display_name": "Getting Started", "description": "Basics for veterans new to the claims process"},
        "building-your-claim": {"display_name": "Building Your Claim", "description": "Evidence, conditions, and preparation guidance"},
        "understanding-your-rating": {"display_name": "Understanding Your Rating", "description": "Rating math, decision letters, and the bilateral factor"},
        "appeals-and-next-steps": {"display_name": "Appeals & Next Steps", "description": "Supplemental claims, higher-level review, board appeal, and TDIU"},
        "special-topics": {"display_name": "Special Topics", "description": "PACT Act, presumptive conditions, and more"},
    }

    articles = db.query(EducationalContent).filter(
        EducationalContent.is_published == True,
        EducationalContent.section.isnot(None)
    ).order_by(
        EducationalContent.section,
        EducationalContent.section_order
    ).all()

    sections = {}
    for article in articles:
        sec = article.section
        if sec not in sections:
            meta = section_definitions.get(sec, {"display_name": sec, "description": ""})
            sections[sec] = {
                "section_id": sec,
                "display_name": meta["display_name"],
                "description": meta["description"],
                "articles": []
            }
        sections[sec]["articles"].append(article.to_dict())

    # Return in defined order
    ordered_sections = []
    for sec_id in ["getting-started", "building-your-claim", "understanding-your-rating", "appeals-and-next-steps", "special-topics"]:
        if sec_id in sections:
            ordered_sections.append(sections[sec_id])

    return {"sections": ordered_sections}
```

**IMPORTANT:** The `/sections` route MUST be defined BEFORE the `/{content_id}` route in the file, otherwise FastAPI will try to match "sections" as a content_id.

### Step 3: Create resource-links endpoint

**File to CREATE:** `/ganuda/vetassist/backend/app/api/v1/endpoints/resource_links.py`

Create a new endpoint module for external resource links:

```python
"""
Resource Links API Endpoint
Serves curated external links to VA.gov and reputable veteran resource sites.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from typing import Optional
from app.database import get_db, Base

router = APIRouter()


class ResourceLink(Base):
    __tablename__ = "vetassist_resource_links"

    id = Column(Integer, primary_key=True)
    title = Column(String(300), nullable=False)
    url = Column(Text, nullable=False, unique=True)
    description = Column(Text)
    section = Column(String(50), nullable=False)
    link_category = Column(String(20), nullable=False, default='stable')
    source_org = Column(String(100))
    last_checked = Column(DateTime(timezone=True))
    last_status = Column(Integer)
    last_redirect_url = Column(Text)
    check_frequency = Column(String(20), default='weekly')
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "description": self.description,
            "section": self.section,
            "link_category": self.link_category,
            "source_org": self.source_org,
            "display_order": self.display_order,
        }


@router.get("")
async def list_resource_links(
    section: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List active resource links, optionally filtered by section or category."""
    query = db.query(ResourceLink).filter(ResourceLink.is_active == True)

    if section:
        query = query.filter(ResourceLink.section == section)
    if category:
        query = query.filter(ResourceLink.link_category == category)

    links = query.order_by(ResourceLink.section, ResourceLink.display_order).all()

    return {
        "total": len(links),
        "links": [link.to_dict() for link in links]
    }


@router.get("/by-section")
async def resource_links_by_section(db: Session = Depends(get_db)):
    """Return resource links grouped by section."""
    links = db.query(ResourceLink).filter(
        ResourceLink.is_active == True
    ).order_by(
        ResourceLink.section, ResourceLink.display_order
    ).all()

    sections = {}
    for link in links:
        if link.section not in sections:
            sections[link.section] = []
        sections[link.section].append(link.to_dict())

    return {"sections": sections}
```

### Step 4: Register the resource-links router in the API

**File:** `/ganuda/vetassist/backend/app/api/v1/__init__.py`

Add the import and router registration. Find the existing imports line and add `resource_links`:

In the import line that includes `evidence_checklist`, add `resource_links`:

```python
from app.api.v1.endpoints import calculator, health, content, chat, auth, evidence_analysis, workbench, wizard, readiness, family, export, dashboard, research, conditions, va_auth, claims, rag, documents, evidence, evidence_checklist, resource_links
```

Then add the router registration at the end of the file (after the evidence_checklist registration):

```python
api_router.include_router(
    resource_links.router,
    prefix="/resource-links",
    tags=["resource-links"]
)
```

---

## Verification

After all 4 steps, verify:

```bash
# 1. Check the sections endpoint returns grouped articles
curl -s http://192.168.132.223:8001/api/v1/content/sections | python3 -m json.tool | head -30

# 2. Check section filtering works on the list endpoint
curl -s "http://192.168.132.223:8001/api/v1/content?section=getting-started" | python3 -m json.tool | head -20

# 3. Check resource links endpoint
curl -s http://192.168.132.223:8001/api/v1/resource-links | python3 -m json.tool | head -30

# 4. Check resource links by section
curl -s http://192.168.132.223:8001/api/v1/resource-links/by-section | python3 -m json.tool | head -30

# 5. Check single article now includes section and author fields
curl -s http://192.168.132.223:8001/api/v1/content/understanding-va-disability-claims | python3 -m json.tool | grep -E "section|author|status|content_version"
```

---

## Success Criteria

- [ ] `to_dict()` returns `section`, `section_order`, `author`, `status`, `content_version`, `source_references`
- [ ] `GET /api/v1/content?section=getting-started` returns only articles in that section
- [ ] `GET /api/v1/content/sections` returns articles grouped by 5 sections in correct order
- [ ] `GET /api/v1/resource-links` returns all 18 active external links
- [ ] `GET /api/v1/resource-links?section=getting-started` returns only links for that section
- [ ] `GET /api/v1/resource-links/by-section` returns links grouped by section
- [ ] Existing endpoints (`GET /content`, `GET /content/search`, `GET /content/{id}`, `GET /content/tags/list`) still work unchanged
- [ ] Backend starts without import errors

---

## Security Notes

- No authentication required for read-only content and link endpoints (public educational material)
- Resource links endpoint only exposes active links (`is_active = true`) — broken links are hidden
- Internal fields (reviewer, review_notes, review_audit_hash) are NOT exposed in the API
- No write endpoints created — content management is done via scripts and the Jr queue

---

## Files

| File | Action | Purpose |
|------|--------|---------|
| `/ganuda/vetassist/backend/app/models/content.py` | MODIFY | Add KB column definitions + update to_dict() |
| `/ganuda/vetassist/backend/app/api/v1/endpoints/content.py` | MODIFY | Add section filter + /sections endpoint |
| `/ganuda/vetassist/backend/app/api/v1/endpoints/resource_links.py` | CREATE | New resource links endpoint |
| `/ganuda/vetassist/backend/app/api/v1/__init__.py` | MODIFY | Register resource_links router |

---

*Cherokee AI Federation — For Seven Generations*
