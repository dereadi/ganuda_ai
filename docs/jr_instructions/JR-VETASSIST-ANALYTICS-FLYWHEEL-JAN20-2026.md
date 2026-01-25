# Jr Instruction: VetAssist Analytics & Learning Flywheel
## Cherokee AI Federation - For Seven Generations
### Priority: HIGH | Sprint 5 Foundation

## Objective

Implement a data collection and learning system for VetAssist that captures anonymized user interactions, learns from patterns, and provides increasingly intelligent recommendations to help veterans succeed with their claims.

## Background

VetAssist currently helps veterans prepare claims, but each session is isolated. By capturing what works (and what doesn't), we can create a flywheel where every user contributes to helping future veterans.

## Implementation Tasks

### Task 1: Backend Analytics Service

Create `/ganuda/vetassist/backend/app/services/analytics_service.py`:

```python
"""
VetAssist Analytics Service
Captures anonymized usage data for learning
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib
import json
from sqlalchemy.orm import Session
from app.core.config import settings

class AnalyticsService:
    """Service for capturing and analyzing VetAssist usage"""

    def __init__(self):
        self.pii_salt = settings.PII_TOKEN_SALT

    def anonymize_session(self, session_id: str) -> str:
        """Create anonymous hash of session"""
        return hashlib.sha256(
            f"{session_id}{self.pii_salt}".encode()
        ).hexdigest()[:16]

    async def track_event(
        self,
        db: Session,
        event_type: str,
        session_id: str,
        event_data: Dict[str, Any],
        metadata: Optional[Dict] = None
    ):
        """Track an analytics event"""
        # Implementation: Insert into vetassist_analytics table
        pass

    async def track_condition_selected(
        self,
        db: Session,
        session_id: str,
        condition_code: str,
        condition_name: str
    ):
        """Track when user selects a condition to claim"""
        pass

    async def track_evidence_uploaded(
        self,
        db: Session,
        session_id: str,
        evidence_category: str,
        file_type: str
    ):
        """Track evidence uploads (no file content)"""
        pass

    async def track_rating_calculated(
        self,
        db: Session,
        session_id: str,
        ratings: List[int],
        combined_rating: int
    ):
        """Track calculator usage"""
        pass

    async def track_wizard_completion(
        self,
        db: Session,
        session_id: str,
        wizard_type: str,
        steps_completed: int,
        total_steps: int,
        conditions_claimed: List[str],
        evidence_categories: List[str]
    ):
        """Track wizard session completion"""
        pass

    async def track_outcome_reported(
        self,
        db: Session,
        session_id: str,
        claim_result: str,  # approved, denied, partial
        rating_received: Optional[int],
        days_to_decision: Optional[int]
    ):
        """Track user-reported outcomes (opt-in)"""
        pass

analytics_service = AnalyticsService()
```

### Task 2: Database Schema

Create migration for analytics tables:

```sql
-- VetAssist Analytics Tables
-- Stores anonymized usage data for learning

CREATE TABLE IF NOT EXISTS vetassist_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    anonymous_session_id VARCHAR(32) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes for analysis
    INDEX idx_analytics_event_type (event_type),
    INDEX idx_analytics_created_at (created_at),
    INDEX idx_analytics_session (anonymous_session_id)
);

-- Aggregated condition success data
CREATE TABLE IF NOT EXISTS vetassist_condition_insights (
    id SERIAL PRIMARY KEY,
    condition_code VARCHAR(10) NOT NULL,
    condition_name VARCHAR(255) NOT NULL,

    -- Aggregated metrics
    total_claims INTEGER DEFAULT 0,
    reported_approvals INTEGER DEFAULT 0,
    reported_denials INTEGER DEFAULT 0,
    avg_rating_received DECIMAL(5,2),
    avg_days_to_decision INTEGER,

    -- Common evidence patterns
    common_evidence_types JSONB DEFAULT '[]',
    success_evidence_correlation JSONB DEFAULT '{}',

    -- Updated by batch job
    last_computed_at TIMESTAMP WITH TIME ZONE,

    UNIQUE(condition_code)
);

-- Forum/external knowledge base
CREATE TABLE IF NOT EXISTS vetassist_knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(64) NOT NULL,  -- reddit, hadit, vetassist_forum
    source_url TEXT,

    topic_category VARCHAR(64),  -- condition, evidence, process, appeal
    condition_codes TEXT[],      -- related conditions if applicable

    content_summary TEXT NOT NULL,
    key_insights JSONB DEFAULT '[]',

    upvotes INTEGER DEFAULT 0,
    relevance_score DECIMAL(5,2) DEFAULT 0.5,

    crawled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User-submitted tips (opt-in)
CREATE TABLE IF NOT EXISTS vetassist_community_tips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    anonymous_user_id VARCHAR(32) NOT NULL,

    tip_category VARCHAR(64) NOT NULL,
    condition_code VARCHAR(10),

    tip_content TEXT NOT NULL,
    evidence_types_mentioned TEXT[],

    helpful_votes INTEGER DEFAULT 0,
    verified BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Task 3: Event Tracking Endpoints

Add to `/ganuda/vetassist/backend/app/api/v1/endpoints/analytics.py`:

```python
"""
Analytics Endpoints - VetAssist Usage Tracking
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.analytics_service import analytics_service

router = APIRouter()

class TrackEventRequest(BaseModel):
    session_id: str
    event_type: str
    event_data: Dict[str, Any] = {}

class TrackOutcomeRequest(BaseModel):
    session_id: str
    claim_result: str  # approved, denied, partial
    rating_received: Optional[int] = None
    days_to_decision: Optional[int] = None
    tips_for_others: Optional[str] = None

@router.post("/track")
async def track_event(
    request: TrackEventRequest,
    db: Session = Depends(get_db)
):
    """Track a general analytics event"""
    await analytics_service.track_event(
        db=db,
        event_type=request.event_type,
        session_id=request.session_id,
        event_data=request.event_data
    )
    return {"success": True}

@router.post("/outcome")
async def report_outcome(
    request: TrackOutcomeRequest,
    db: Session = Depends(get_db)
):
    """User voluntarily reports their claim outcome"""
    await analytics_service.track_outcome_reported(
        db=db,
        session_id=request.session_id,
        claim_result=request.claim_result,
        rating_received=request.rating_received,
        days_to_decision=request.days_to_decision
    )
    return {"success": True, "message": "Thank you for helping future veterans!"}

@router.get("/insights/{condition_code}")
async def get_condition_insights(
    condition_code: str,
    db: Session = Depends(get_db)
):
    """Get aggregated insights for a condition"""
    # Return anonymized, aggregated data
    pass
```

### Task 4: Frontend Event Tracking Hook

Create `/ganuda/vetassist/frontend/src/hooks/useAnalytics.ts`:

```typescript
/**
 * VetAssist Analytics Hook
 * Tracks user interactions for learning system
 */
import { useCallback } from 'react';

const ANALYTICS_ENDPOINT = '/api/v1/analytics/track';

interface AnalyticsEvent {
  event_type: string;
  event_data: Record<string, any>;
}

export function useAnalytics(sessionId: string) {
  const trackEvent = useCallback(async (event: AnalyticsEvent) => {
    try {
      await fetch(ANALYTICS_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          ...event
        })
      });
    } catch (error) {
      // Silent fail - analytics should never block user
      console.debug('Analytics event failed:', error);
    }
  }, [sessionId]);

  return {
    trackConditionSelected: (code: string, name: string) =>
      trackEvent({
        event_type: 'condition_selected',
        event_data: { condition_code: code, condition_name: name }
      }),

    trackEvidenceUploaded: (category: string, fileType: string) =>
      trackEvent({
        event_type: 'evidence_uploaded',
        event_data: { category, file_type: fileType }
      }),

    trackRatingCalculated: (ratings: number[], combined: number) =>
      trackEvent({
        event_type: 'rating_calculated',
        event_data: { ratings, combined_rating: combined }
      }),

    trackWizardStep: (step: number, stepName: string) =>
      trackEvent({
        event_type: 'wizard_step',
        event_data: { step, step_name: stepName }
      }),

    trackChatQuestion: (topic: string) =>
      trackEvent({
        event_type: 'chat_question',
        event_data: { topic }
      })
  };
}
```

### Task 5: Forum Crawler (Phase 2)

Create `/ganuda/vetassist/backend/app/services/forum_crawler.py`:

```python
"""
Veteran Forum Crawler
Extracts insights from public veteran communities
"""
import asyncio
from typing import List, Dict
from datetime import datetime
# Will use Crawl4AI for extraction

class VeteranForumCrawler:
    """Crawls and extracts insights from veteran forums"""

    SOURCES = {
        'reddit': {
            'url': 'https://www.reddit.com/r/VeteransBenefits/',
            'type': 'reddit',
            'selectors': {...}
        },
        'hadit': {
            'url': 'https://www.hadit.com/forums/',
            'type': 'forum',
            'selectors': {...}
        }
    }

    async def crawl_source(self, source_name: str) -> List[Dict]:
        """Crawl a single source for insights"""
        pass

    async def extract_insights(self, content: str) -> Dict:
        """Use LLM to extract structured insights"""
        pass

    async def categorize_by_condition(self, insight: Dict) -> List[str]:
        """Map insight to VA condition codes"""
        pass

    async def run_daily_crawl(self):
        """Daily crawl job for fresh insights"""
        pass
```

### Task 6: Recommendation Engine (Phase 3)

```python
"""
VetAssist Recommendation Engine
Provides intelligent suggestions based on collected data
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

class RecommendationEngine:
    """Generates recommendations based on analytics data"""

    async def get_evidence_recommendations(
        self,
        db: Session,
        condition_codes: List[str]
    ) -> List[Dict]:
        """Recommend evidence types based on success patterns"""
        pass

    async def get_related_conditions(
        self,
        db: Session,
        condition_code: str
    ) -> List[Dict]:
        """Suggest commonly co-filed conditions"""
        pass

    async def get_success_tips(
        self,
        db: Session,
        condition_code: str
    ) -> List[str]:
        """Get community tips for a condition"""
        pass

    async def estimate_timeline(
        self,
        db: Session,
        condition_codes: List[str]
    ) -> Dict:
        """Estimate decision timeline based on historical data"""
        pass
```

## Integration Points

1. **Wizard Flow** - Track each step completion
2. **Calculator** - Track rating explorations
3. **Chat** - Track question topics
4. **Evidence Upload** - Track categories (not content)
5. **Export** - Track form generation

## Privacy Requirements

- All session IDs must be hashed before storage
- No PII in analytics tables
- File contents never stored
- Users can opt-out of analytics
- Data only used to improve VetAssist

## Success Criteria

- [ ] Analytics service implemented
- [ ] Database tables created
- [ ] Frontend tracking hook integrated
- [ ] Events flowing to database
- [ ] Basic insights dashboard working
- [ ] Privacy controls in place

## Reference Documents

- `/ganuda/docs/vetassist/VETASSIST-DATA-FLYWHEEL-STRATEGY.md`
- `/ganuda/docs/vetassist/VetAssist-PRD-v1.md`

---
*Cherokee AI Federation - For Seven Generations*
