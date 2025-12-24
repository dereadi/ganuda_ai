# JR INSTRUCTION: SAG Governance Enhancement & Resource Intelligence

**Created**: December 23, 2025  
**Priority**: P1 (Council Mandated)  
**Council Vote**: 659655e7824239fb (82.5% confidence)  
**Assigned To**: Gecko Jr (Technical Integration), Spider Jr (Cultural Integration)  
**Estimated Complexity**: HIGH  
**Phase**: 3 - Hardening & Packaging

---

## ULTRATHINK ANALYSIS

### The Core Problem

The Council identified a critical gap in the Cherokee AI Federation:

> "The infrastructure behaves like a control room. The UI behaves like a status board."

**Symptoms**:
- Governance is invisible
- Authority is implicit, not explicit
- Operators must remember instead of see
- Safety mechanisms exist but are not surfaced

**Root Cause**: The SAG UI was built to display information, not to embody control. It shows what IS, but not:
- What CAN be changed
- What CANNOT be changed
- What REQUIRES approval
- What HAS changed and why

### The Dual Mission

This instruction addresses TWO interconnected requirements:

1. **GOVERNANCE SURFACING** (Council Priority)
   - Make constitutional constraints visible
   - Show pending changes requiring approval
   - Display authority boundaries
   - Surface cognitive health metrics

2. **SAG RESOURCE INTELLIGENCE** (Pilot Requirement)
   - Chat interface for resource queries
   - Productive API integration
   - Smartsheet API integration
   - Resource availability, skills, allocations

### Why These Must Be Combined

The resource intelligence system IS a governance challenge:
- Who can query sensitive allocation data?
- Who can modify assignments?
- What approvals are needed?
- How is access audited?

By building governance INTO the resource system from the start, we avoid the "invisible governance" anti-pattern that the Council identified.

---

## ARCHITECTURAL VISION

### Four-Plane Alignment

The enhanced SAG UI must touch all four planes:

```
┌─────────────────────────────────────────────────────────────────┐
│                     SAG UNIFIED INTERFACE                        │
├─────────────────────────────────────────────────────────────────┤
│  COGNITIVE PLANE                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                │
│  │ Council     │ │ Resource    │ │ Thermal     │                │
│  │ Voting      │ │ Intelligence│ │ Memory      │                │
│  │ Interface   │ │ Chat        │ │ Browser     │                │
│  └─────────────┘ └─────────────┘ └─────────────┘                │
├─────────────────────────────────────────────────────────────────┤
│  EXECUTION PLANE                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                │
│  │ Jr Task     │ │ API         │ │ Service     │                │
│  │ Dashboard   │ │ Integrations│ │ Controls    │                │
│  └─────────────┘ └─────────────┘ └─────────────┘                │
├─────────────────────────────────────────────────────────────────┤
│  MEMORY & STATE PLANE                                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                │
│  │ Session     │ │ Resource    │ │ Audit       │                │
│  │ Persistence │ │ Cache       │ │ Trail       │                │
│  └─────────────┘ └─────────────┘ └─────────────┘                │
├─────────────────────────────────────────────────────────────────┤
│  GOVERNANCE PLANE (NEW - PRIMARY FOCUS)                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                │
│  │ Constraint  │ │ Approval    │ │ Authority   │                │
│  │ Badges      │ │ Queue       │ │ Map         │                │
│  └─────────────┘ └─────────────┘ └─────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

---

## PART 1: GOVERNANCE SURFACING

### 1.1 Constitutional Constraint Badges

Every action in the UI must display its governance status.

**Badge Types**:

| Badge | Meaning | Color | Icon |
|-------|---------|-------|------|
| 🔓 OPEN | No restrictions | Green | Unlocked |
| 🔒 LOCKED | Cannot be changed | Red | Locked |
| ⚠️ COUNCIL | Requires Council vote | Yellow | Warning |
| 👤 TPM | Requires TPM approval | Blue | Person |
| 📋 AUDIT | Action will be logged | Gray | Clipboard |

**Implementation**:

```python
# /ganuda/lib/governance_badges.py

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
import psycopg2

class GovernanceLevel(Enum):
    OPEN = "open"
    LOCKED = "locked"
    COUNCIL_REQUIRED = "council"
    TPM_REQUIRED = "tpm"
    AUDIT_ONLY = "audit"

@dataclass
class GovernanceBadge:
    level: GovernanceLevel
    reason: str
    constraint_name: Optional[str] = None
    override_possible: bool = False
    override_requires: Optional[str] = None

class GovernanceChecker:
    """
    Checks governance requirements for any action.
    
    Usage:
        checker = GovernanceChecker()
        badge = checker.check_action("restart_service", target="llm_gateway")
        if badge.level == GovernanceLevel.COUNCIL_REQUIRED:
            # Show council vote UI
    """
    
    # Constitutional constraints from thermal memory
    CONSTRAINTS = {
        "no_push_main": {
            "level": GovernanceLevel.LOCKED,
            "reason": "Direct push to main/master requires PR review",
            "actions": ["git_push_main", "git_push_master"]
        },
        "no_external_data_transmission": {
            "level": GovernanceLevel.LOCKED,
            "reason": "External data transmission violates data sovereignty",
            "actions": ["send_external", "upload_cloud", "sync_external"]
        },
        "no_production_delete": {
            "level": GovernanceLevel.TPM_REQUIRED,
            "reason": "Destructive database operations require human approval",
            "actions": ["delete_table", "drop_database", "truncate"]
        },
        "service_restart": {
            "level": GovernanceLevel.AUDIT_ONLY,
            "reason": "Service restarts are logged for operational awareness",
            "actions": ["restart_service", "stop_service"]
        },
        "resource_allocation_change": {
            "level": GovernanceLevel.COUNCIL_REQUIRED,
            "reason": "Resource allocation changes affect tribal operations",
            "actions": ["change_allocation", "assign_resource", "remove_assignment"]
        },
        "api_key_management": {
            "level": GovernanceLevel.TPM_REQUIRED,
            "reason": "API key creation/revocation requires TPM approval",
            "actions": ["create_api_key", "revoke_api_key", "rotate_key"]
        }
    }
    
    def check_action(self, action: str, target: str = None) -> GovernanceBadge:
        """Check governance requirements for an action."""
        for constraint_name, constraint in self.CONSTRAINTS.items():
            if action in constraint["actions"]:
                return GovernanceBadge(
                    level=GovernanceLevel(constraint["level"]),
                    reason=constraint["reason"],
                    constraint_name=constraint_name,
                    override_possible=constraint.get("override_possible", False),
                    override_requires=constraint.get("override_requires")
                )
        
        # Default: audited but open
        return GovernanceBadge(
            level=GovernanceLevel.AUDIT_ONLY,
            reason="Standard action - will be logged",
            constraint_name=None
        )
    
    def get_all_constraints(self) -> List[dict]:
        """Return all constraints for UI display."""
        return [
            {
                "name": name,
                "level": c["level"].value if isinstance(c["level"], GovernanceLevel) else c["level"],
                "reason": c["reason"],
                "affected_actions": c["actions"]
            }
            for name, c in self.CONSTRAINTS.items()
        ]
```

### 1.2 Pending Approvals Queue

Surface all pending changes that require approval.

**Database Schema**:

```sql
-- Pending approvals table
CREATE TABLE IF NOT EXISTS pending_approvals (
    approval_id SERIAL PRIMARY KEY,
    
    -- What needs approval
    action_type VARCHAR(64) NOT NULL,
    target_resource VARCHAR(256),
    proposed_change JSONB NOT NULL,
    
    -- Governance
    required_level VARCHAR(32) NOT NULL,  -- 'council', 'tpm', 'peer'
    constraint_triggered VARCHAR(64),
    
    -- Requester
    requested_by VARCHAR(128) NOT NULL,
    requested_via VARCHAR(32),  -- 'ui', 'api', 'telegram', 'jr_agent'
    requested_at TIMESTAMP DEFAULT NOW(),
    
    -- Status
    status VARCHAR(32) DEFAULT 'pending',  -- 'pending', 'approved', 'rejected', 'expired'
    
    -- Resolution
    resolved_by VARCHAR(128),
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    council_vote_hash VARCHAR(16),
    
    -- Expiry
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '24 hours'
);

CREATE INDEX idx_pending_status ON pending_approvals(status, required_level);
CREATE INDEX idx_pending_expires ON pending_approvals(expires_at) WHERE status = 'pending';
```

**API Endpoint**:

```python
# Add to gateway.py

@app.route('/v1/governance/pending', methods=['GET'])
def get_pending_approvals():
    """Get all pending approvals for the current user's authority level."""
    api_key = validate_api_key(request)
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT 
                    approval_id,
                    action_type,
                    target_resource,
                    proposed_change,
                    required_level,
                    requested_by,
                    requested_at,
                    expires_at,
                    EXTRACT(EPOCH FROM (expires_at - NOW())) as seconds_remaining
                FROM pending_approvals
                WHERE status = 'pending'
                AND expires_at > NOW()
                ORDER BY 
                    CASE required_level
                        WHEN 'council' THEN 1
                        WHEN 'tpm' THEN 2
                        ELSE 3
                    END,
                    requested_at ASC
            """)
            
            return jsonify({
                "pending_count": cur.rowcount,
                "approvals": [dict(row) for row in cur.fetchall()]
            })

@app.route('/v1/governance/approve/<int:approval_id>', methods=['POST'])
def approve_change(approval_id):
    """Approve a pending change (TPM or authorized role only)."""
    api_key = validate_api_key(request)
    data = request.json
    
    # Check authority
    if not has_approval_authority(api_key, approval_id):
        return jsonify({"error": "Insufficient authority"}), 403
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE pending_approvals
                SET status = 'approved',
                    resolved_by = %s,
                    resolved_at = NOW(),
                    resolution_notes = %s
                WHERE approval_id = %s
                AND status = 'pending'
                RETURNING *
            """, (api_key['owner'], data.get('notes', ''), approval_id))
            
            if cur.rowcount == 0:
                return jsonify({"error": "Approval not found or already resolved"}), 404
            
            conn.commit()
            
            # Execute the approved action
            approved = cur.fetchone()
            execute_approved_action(approved)
            
            return jsonify({"status": "approved", "approval_id": approval_id})
```

### 1.3 Authority Map

Visual display of who can do what.

**UI Component** (React/Flask template):

```html
<!-- templates/governance/authority_map.html -->

<div class="authority-map">
    <h2>🏛️ Authority Map</h2>
    <p class="subtitle">Who can do what in the Cherokee AI Federation</p>
    
    <div class="authority-grid">
        <!-- TPM Authority -->
        <div class="authority-card tpm">
            <div class="card-header">
                <span class="icon">👤</span>
                <h3>TPM (Technical Program Manager)</h3>
            </div>
            <ul class="permissions">
                <li class="can">✅ Approve Jr task execution</li>
                <li class="can">✅ Create/revoke API keys</li>
                <li class="can">✅ Override Council decisions (logged)</li>
                <li class="can">✅ Access all thermal memories</li>
                <li class="cannot">❌ Direct code execution</li>
                <li class="cannot">❌ Push to main without PR</li>
            </ul>
        </div>
        
        <!-- Council Authority -->
        <div class="authority-card council">
            <div class="card-header">
                <span class="icon">🏛️</span>
                <h3>7-Specialist Council</h3>
            </div>
            <ul class="permissions">
                <li class="can">✅ Vote on architectural decisions</li>
                <li class="can">✅ Approve resource allocations</li>
                <li class="can">✅ Flag concerns (any specialist)</li>
                <li class="can">✅ Block unsafe changes (any concern)</li>
                <li class="cannot">❌ Execute code directly</li>
                <li class="cannot">❌ Override TPM without vote</li>
            </ul>
        </div>
        
        <!-- Jr Agents Authority -->
        <div class="authority-card jr">
            <div class="card-header">
                <span class="icon">🤖</span>
                <h3>Jr Agents</h3>
            </div>
            <ul class="permissions">
                <li class="can">✅ Bid on announced tasks</li>
                <li class="can">✅ Execute approved tasks</li>
                <li class="can">✅ Write to thermal memory</li>
                <li class="can">✅ Query Council for guidance</li>
                <li class="cannot">❌ Create API keys</li>
                <li class="cannot">❌ Modify production data without approval</li>
                <li class="cannot">❌ Access external networks</li>
            </ul>
        </div>
        
        <!-- API Users Authority -->
        <div class="authority-card api">
            <div class="card-header">
                <span class="icon">🔑</span>
                <h3>API Users</h3>
            </div>
            <ul class="permissions">
                <li class="can">✅ Query LLM endpoints</li>
                <li class="can">✅ Submit Council votes</li>
                <li class="can">✅ Read thermal memories (scoped)</li>
                <li class="cannot">❌ Modify system configuration</li>
                <li class="cannot">❌ Access other users' data</li>
            </ul>
        </div>
    </div>
    
    <!-- Active Constraints -->
    <div class="active-constraints">
        <h3>🔒 Active Constitutional Constraints</h3>
        <div id="constraint-list">
            {% for constraint in constraints %}
            <div class="constraint-badge {{ constraint.level }}">
                <span class="constraint-name">{{ constraint.name }}</span>
                <span class="constraint-reason">{{ constraint.reason }}</span>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
```

### 1.4 Cognitive Health Dashboard

Surface the "mental state" of the Federation.

```python
# /ganuda/lib/cognitive_health.py

def get_cognitive_health_metrics():
    """
    Return cognitive health metrics for dashboard display.
    
    These are first-class operational metrics, not just CPU/memory.
    """
    conn = get_db_connection()
    metrics = {}
    
    with conn.cursor() as cur:
        # Thermal Memory Pressure
        cur.execute("""
            SELECT 
                COUNT(*) as total_memories,
                COUNT(*) FILTER (WHERE temperature_score > 80) as hot_memories,
                COUNT(*) FILTER (WHERE temperature_score > 90) as critical_memories,
                AVG(temperature_score) as avg_temperature
            FROM thermal_memory_archive
            WHERE created_at > NOW() - INTERVAL '24 hours'
        """)
        thermal = cur.fetchone()
        metrics['thermal_pressure'] = {
            'total_24h': thermal[0],
            'hot_count': thermal[1],
            'critical_count': thermal[2],
            'avg_temp': round(thermal[3] or 0, 1),
            'status': 'critical' if thermal[2] > 10 else 'warning' if thermal[1] > 20 else 'healthy'
        }
        
        # Memory Redundancy (A-MEM links)
        cur.execute("""
            SELECT 
                COUNT(*) as total_links,
                COUNT(DISTINCT source_hash) as linked_memories,
                AVG(similarity_score) as avg_similarity
            FROM memory_links
        """)
        links = cur.fetchone()
        metrics['memory_redundancy'] = {
            'total_links': links[0],
            'linked_memories': links[1],
            'avg_similarity': round(links[2] or 0, 3),
            'status': 'healthy' if links[0] > 1000 else 'building'
        }
        
        # Pheromone Decay Health
        cur.execute("""
            SELECT 
                COUNT(*) as total_pheromones,
                AVG(intensity) as avg_intensity,
                COUNT(*) FILTER (WHERE intensity < 0.1) as fading
            FROM stigmergy_pheromones
        """)
        pheromones = cur.fetchone()
        metrics['pheromone_health'] = {
            'total': pheromones[0],
            'avg_intensity': round(pheromones[1] or 0, 3),
            'fading_count': pheromones[2],
            'status': 'healthy' if (pheromones[1] or 0) > 0.3 else 'decaying'
        }
        
        # Council Disagreement Level
        cur.execute("""
            SELECT 
                AVG(confidence) as avg_confidence,
                AVG(concern_count) as avg_concerns,
                COUNT(*) FILTER (WHERE concern_count > 0) as votes_with_concerns
            FROM council_votes
            WHERE voted_at > NOW() - INTERVAL '7 days'
        """)
        council = cur.fetchone()
        metrics['council_health'] = {
            'avg_confidence': round(council[0] or 0, 3),
            'avg_concerns': round(council[1] or 0, 2),
            'concern_rate': round((council[2] or 0) / max(1, council[0] or 1) * 100, 1),
            'status': 'aligned' if (council[0] or 0) > 0.75 else 'deliberating' if (council[0] or 0) > 0.5 else 'conflicted'
        }
        
        # Jr Agent Activity
        cur.execute("""
            SELECT 
                COUNT(DISTINCT agent_id) as active_agents,
                COUNT(*) FILTER (WHERE status = 'completed') as completed_tasks,
                COUNT(*) FILTER (WHERE status = 'failed') as failed_tasks
            FROM jr_task_announcements
            WHERE announced_at > NOW() - INTERVAL '24 hours'
        """)
        jr = cur.fetchone()
        metrics['jr_health'] = {
            'active_agents': jr[0],
            'completed_24h': jr[1],
            'failed_24h': jr[2],
            'success_rate': round(jr[1] / max(1, jr[1] + jr[2]) * 100, 1),
            'status': 'productive' if jr[1] > 5 else 'active' if jr[1] > 0 else 'idle'
        }
    
    conn.close()
    
    # Overall health score
    statuses = [m.get('status', 'unknown') for m in metrics.values()]
    if 'critical' in statuses or 'conflicted' in statuses:
        metrics['overall'] = 'needs_attention'
    elif 'warning' in statuses or 'decaying' in statuses:
        metrics['overall'] = 'monitoring'
    else:
        metrics['overall'] = 'healthy'
    
    return metrics
```

---

## PART 2: SAG RESOURCE INTELLIGENCE

### 2.1 Resource Intelligence Chat Interface

Natural language queries for resource management.

**Example Queries**:
- "Is Bob User available for a special 5 hour consult?"
- "Is any PM available for X work?"
- "Is there a resource that can fill in for Jim User?"
- "Who has Python skills and is free next week?"
- "Show me all allocations for Project Alpha"

**Architecture**:

```
┌─────────────────────────────────────────────────────────────────┐
│                   RESOURCE INTELLIGENCE CHAT                     │
├─────────────────────────────────────────────────────────────────┤
│  User Query                                                      │
│  "Is Bob available for a 5 hour consult next Tuesday?"          │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              QUERY UNDERSTANDING (Council)                  ││
│  │  Intent: check_availability                                 ││
│  │  Entity: person="Bob", duration=5h, date="next Tuesday"     ││
│  │  Governance: requires AUDIT badge (read-only query)         ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │  Productive  │ │  Smartsheet  │ │   Local DB   │            │
│  │     API      │ │     API      │ │   (cache)    │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              RESPONSE SYNTHESIS (Council)                   ││
│  │  "Bob has 3 hours allocated to Project X on Tuesday.       ││
│  │   He could accommodate 5 hours if Project X is flexed.     ││
│  │   [📋 AUDIT: Query logged] [⚠️ COUNCIL: Change requires    ││
│  │   approval]"                                                ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Productive API Integration

```python
# /ganuda/lib/productive_client.py

import requests
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import os

class ProductiveClient:
    """
    Client for Productive.io API.
    
    API Docs: https://developer.productive.io/
    
    Note: Respects rate limits (150 requests per 20 seconds)
    """
    
    BASE_URL = "https://api.productive.io/api/v2"
    
    def __init__(self, api_token: str = None, org_id: str = None):
        self.api_token = api_token or os.environ.get('PRODUCTIVE_API_TOKEN')
        self.org_id = org_id or os.environ.get('PRODUCTIVE_ORG_ID')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/vnd.api+json',
            'X-Auth-Token': self.api_token,
            'X-Organization-Id': self.org_id
        })
    
    def get_people(self, filters: Dict = None) -> List[Dict]:
        """Get all people (resources) with optional filters."""
        params = {}
        if filters:
            for key, value in filters.items():
                params[f'filter[{key}]'] = value
        
        response = self.session.get(f"{self.BASE_URL}/people", params=params)
        response.raise_for_status()
        return response.json()['data']
    
    def get_person_by_name(self, name: str) -> Optional[Dict]:
        """Find a person by name (fuzzy match)."""
        people = self.get_people()
        name_lower = name.lower()
        
        for person in people:
            full_name = f"{person['attributes'].get('first_name', '')} {person['attributes'].get('last_name', '')}".lower()
            if name_lower in full_name:
                return person
        
        return None
    
    def get_person_availability(self, person_id: str, 
                                 start_date: datetime = None,
                                 end_date: datetime = None) -> Dict:
        """
        Get a person's availability for a date range.
        
        Returns:
            {
                'person_id': str,
                'person_name': str,
                'date_range': {'start': str, 'end': str},
                'total_capacity_hours': float,
                'allocated_hours': float,
                'available_hours': float,
                'allocations': [...]
            }
        """
        if not start_date:
            start_date = datetime.now()
        if not end_date:
            end_date = start_date + timedelta(days=7)
        
        # Get bookings/allocations for this person
        params = {
            'filter[person_id]': person_id,
            'filter[after]': start_date.strftime('%Y-%m-%d'),
            'filter[before]': end_date.strftime('%Y-%m-%d')
        }
        
        response = self.session.get(f"{self.BASE_URL}/bookings", params=params)
        response.raise_for_status()
        bookings = response.json()['data']
        
        # Calculate availability
        total_allocated = sum(
            float(b['attributes'].get('time', 0)) / 60  # Convert minutes to hours
            for b in bookings
        )
        
        # Assume 8 hours/day capacity
        business_days = sum(1 for d in range((end_date - start_date).days + 1)
                          if (start_date + timedelta(days=d)).weekday() < 5)
        total_capacity = business_days * 8
        
        return {
            'person_id': person_id,
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            },
            'total_capacity_hours': total_capacity,
            'allocated_hours': total_allocated,
            'available_hours': max(0, total_capacity - total_allocated),
            'allocations': [
                {
                    'project': b['relationships'].get('project', {}).get('data', {}).get('id'),
                    'hours': float(b['attributes'].get('time', 0)) / 60,
                    'date': b['attributes'].get('started_on')
                }
                for b in bookings
            ]
        }
    
    def get_people_with_skill(self, skill: str) -> List[Dict]:
        """Find people with a specific skill."""
        # Note: Productive stores skills in custom fields
        # This may need adjustment based on SAG's Productive configuration
        people = self.get_people()
        
        results = []
        for person in people:
            skills = person['attributes'].get('custom_fields', {}).get('skills', [])
            if skill.lower() in [s.lower() for s in skills]:
                results.append(person)
        
        return results
    
    def find_available_resource(self, 
                                 role: str = None,
                                 skill: str = None,
                                 hours_needed: float = 0,
                                 start_date: datetime = None) -> List[Dict]:
        """
        Find available resources matching criteria.
        
        Args:
            role: PM, Engineer, Designer, etc.
            skill: Specific skill like "Python", "AWS", etc.
            hours_needed: Minimum available hours required
            start_date: When availability is needed
        
        Returns:
            List of people with availability info, sorted by most available
        """
        if not start_date:
            start_date = datetime.now()
        
        # Get all people, optionally filtered by role
        filters = {}
        if role:
            filters['role'] = role
        
        people = self.get_people(filters)
        
        # Check availability for each
        available = []
        for person in people:
            avail = self.get_person_availability(
                person['id'],
                start_date,
                start_date + timedelta(days=7)
            )
            
            if avail['available_hours'] >= hours_needed:
                # Check skill if specified
                if skill:
                    skills = person['attributes'].get('custom_fields', {}).get('skills', [])
                    if skill.lower() not in [s.lower() for s in skills]:
                        continue
                
                available.append({
                    'person': person,
                    'availability': avail
                })
        
        # Sort by most available
        available.sort(key=lambda x: x['availability']['available_hours'], reverse=True)
        
        return available
```

### 2.3 Smartsheet API Integration

```python
# /ganuda/lib/smartsheet_client.py

import requests
from typing import Optional, List, Dict
import os

class SmartsheetClient:
    """
    Client for Smartsheet API.
    
    API Docs: https://smartsheet.redoc.ly/
    
    Note: Using new paginated endpoints per Feb 2026 migration requirements.
    """
    
    BASE_URL = "https://api.smartsheet.com/2.0"
    
    def __init__(self, api_token: str = None):
        self.api_token = api_token or os.environ.get('SMARTSHEET_API_TOKEN')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        })
    
    def _paginate(self, endpoint: str, params: Dict = None) -> List[Dict]:
        """
        Handle token-based pagination (new API pattern).
        
        Per Smartsheet migration: using pageSize and nextPageToken
        instead of deprecated includeAll.
        """
        all_data = []
        params = params or {}
        params['pageSize'] = 100  # Max allowed
        
        while True:
            response = self.session.get(f"{self.BASE_URL}/{endpoint}", params=params)
            response.raise_for_status()
            result = response.json()
            
            all_data.extend(result.get('data', []))
            
            # Check for next page
            next_token = result.get('nextPageToken')
            if not next_token:
                break
            
            params['pageToken'] = next_token
        
        return all_data
    
    def get_sheets(self) -> List[Dict]:
        """Get all sheets accessible to the user."""
        return self._paginate('sheets')
    
    def get_sheet(self, sheet_id: str) -> Dict:
        """Get a specific sheet with rows."""
        response = self.session.get(f"{self.BASE_URL}/sheets/{sheet_id}")
        response.raise_for_status()
        return response.json()
    
    def get_workspaces(self) -> List[Dict]:
        """Get all workspaces (using new metadata endpoint)."""
        return self._paginate('workspaces')
    
    def get_workspace_metadata(self, workspace_id: str) -> Dict:
        """
        Get workspace metadata (new endpoint replacing GET /workspaces/{id}).
        """
        response = self.session.get(
            f"{self.BASE_URL}/workspaces/{workspace_id}/metadata"
        )
        response.raise_for_status()
        return response.json()
    
    def get_workspace_children(self, workspace_id: str, 
                                resource_types: List[str] = None) -> List[Dict]:
        """
        Get workspace children (new endpoint).
        
        Args:
            resource_types: ['folders', 'sheets', 'reports', etc.]
        """
        params = {}
        if resource_types:
            params['childrenResourceTypes'] = ','.join(resource_types)
        
        return self._paginate(
            f'workspaces/{workspace_id}/children',
            params
        )
    
    def search_sheets(self, query: str) -> List[Dict]:
        """Search for sheets by name or content."""
        response = self.session.get(
            f"{self.BASE_URL}/search/sheets",
            params={'query': query}
        )
        response.raise_for_status()
        return response.json().get('results', [])
    
    def get_resource_allocations(self, sheet_id: str) -> List[Dict]:
        """
        Get resource allocations from a resource management sheet.
        
        Assumes SAG has a standard resource allocation sheet format.
        """
        sheet = self.get_sheet(sheet_id)
        
        # Parse columns to find relevant fields
        columns = {col['title']: col['id'] for col in sheet['columns']}
        
        allocations = []
        for row in sheet['rows']:
            cells = {c.get('columnId'): c.get('value') for c in row['cells']}
            
            allocation = {
                'row_id': row['id'],
                'resource': cells.get(columns.get('Resource')),
                'project': cells.get(columns.get('Project')),
                'hours': cells.get(columns.get('Hours')),
                'start_date': cells.get(columns.get('Start Date')),
                'end_date': cells.get(columns.get('End Date')),
                'status': cells.get(columns.get('Status'))
            }
            
            if allocation['resource']:  # Only include rows with a resource
                allocations.append(allocation)
        
        return allocations
```

### 2.4 Resource Intelligence Service

Combines all data sources with governance.

```python
# /ganuda/services/resource_intelligence.py

from lib.productive_client import ProductiveClient
from lib.smartsheet_client import SmartsheetClient
from lib.governance_badges import GovernanceChecker, GovernanceLevel
from lib.specialist_council import query_council
from datetime import datetime, timedelta
import json

class ResourceIntelligenceService:
    """
    Natural language interface for resource queries.
    
    Combines:
    - Productive API (allocations, bookings)
    - Smartsheet API (project data)
    - Council (query understanding, response synthesis)
    - Governance (badges, approvals)
    """
    
    def __init__(self):
        self.productive = ProductiveClient()
        self.smartsheet = SmartsheetClient()
        self.governance = GovernanceChecker()
    
    def process_query(self, query: str, user_context: dict = None) -> dict:
        """
        Process a natural language resource query.
        
        Args:
            query: User's question like "Is Bob available?"
            user_context: Session info, permissions, etc.
        
        Returns:
            {
                'answer': str,
                'data': dict,
                'governance': GovernanceBadge,
                'sources': list,
                'suggested_actions': list
            }
        """
        # Step 1: Use Council to understand the query
        understanding = self._understand_query(query)
        
        # Step 2: Check governance for this query type
        badge = self.governance.check_action(
            understanding['intent'],
            understanding.get('target')
        )
        
        # Step 3: Execute the query against appropriate sources
        if badge.level == GovernanceLevel.LOCKED:
            return {
                'answer': f"This query is blocked: {badge.reason}",
                'governance': badge,
                'data': None
            }
        
        data = self._execute_query(understanding)
        
        # Step 4: Synthesize response with governance context
        response = self._synthesize_response(query, understanding, data, badge)
        
        return response
    
    def _understand_query(self, query: str) -> dict:
        """Use Council to parse the query intent and entities."""
        # Query the council for understanding
        result = query_council(
            question=f"Parse this resource query into intent and entities: '{query}'",
            context="Resource intelligence system. Intents: check_availability, find_resource, show_allocations, change_allocation, show_skills. Extract: person names, dates, durations, skills, projects.",
            options=["check_availability", "find_resource", "show_allocations", "change_allocation", "show_skills"]
        )
        
        # Parse council response into structured format
        # This is simplified - real implementation would use more sophisticated NLU
        understanding = {
            'original_query': query,
            'intent': 'check_availability',  # Default
            'entities': {}
        }
        
        # Simple entity extraction
        query_lower = query.lower()
        
        if 'available' in query_lower or 'free' in query_lower:
            understanding['intent'] = 'check_availability'
        elif 'find' in query_lower or 'who can' in query_lower or 'any' in query_lower:
            understanding['intent'] = 'find_resource'
        elif 'allocation' in query_lower or 'assigned' in query_lower:
            understanding['intent'] = 'show_allocations'
        elif 'skill' in query_lower:
            understanding['intent'] = 'show_skills'
        
        # Extract hours if mentioned
        import re
        hours_match = re.search(r'(\d+)\s*hour', query_lower)
        if hours_match:
            understanding['entities']['hours_needed'] = int(hours_match.group(1))
        
        # Extract role if mentioned
        for role in ['pm', 'engineer', 'designer', 'architect']:
            if role in query_lower:
                understanding['entities']['role'] = role.upper()
                break
        
        return understanding
    
    def _execute_query(self, understanding: dict) -> dict:
        """Execute the query against data sources."""
        intent = understanding['intent']
        entities = understanding.get('entities', {})
        
        if intent == 'check_availability':
            # Find the person and check their availability
            person_name = entities.get('person_name', '')
            person = self.productive.get_person_by_name(person_name)
            
            if person:
                return self.productive.get_person_availability(person['id'])
            else:
                return {'error': f"Could not find person: {person_name}"}
        
        elif intent == 'find_resource':
            return self.productive.find_available_resource(
                role=entities.get('role'),
                skill=entities.get('skill'),
                hours_needed=entities.get('hours_needed', 0)
            )
        
        elif intent == 'show_allocations':
            # Get from both Productive and Smartsheet
            productive_data = self.productive.get_people()
            # smartsheet_data = self.smartsheet.get_resource_allocations(SHEET_ID)
            return {'productive': productive_data}
        
        return {'error': 'Unknown intent'}
    
    def _synthesize_response(self, query: str, understanding: dict, 
                             data: dict, badge) -> dict:
        """Create human-readable response with governance context."""
        
        if 'error' in data:
            answer = f"I couldn't complete that query: {data['error']}"
        elif understanding['intent'] == 'check_availability':
            avail = data.get('available_hours', 0)
            alloc = data.get('allocated_hours', 0)
            answer = f"Available hours: {avail}h (currently allocated: {alloc}h)"
        elif understanding['intent'] == 'find_resource':
            if data:
                names = [r['person']['attributes'].get('first_name', 'Unknown') 
                        for r in data[:5]]
                answer = f"Found {len(data)} available resources: {', '.join(names)}"
            else:
                answer = "No resources found matching your criteria."
        else:
            answer = "Query processed. See data for details."
        
        # Add governance badge to response
        badge_text = {
            GovernanceLevel.OPEN: "🔓",
            GovernanceLevel.AUDIT_ONLY: "📋",
            GovernanceLevel.TPM_REQUIRED: "👤",
            GovernanceLevel.COUNCIL_REQUIRED: "⚠️",
            GovernanceLevel.LOCKED: "🔒"
        }.get(badge.level, "")
        
        return {
            'answer': f"{answer} {badge_text}",
            'data': data,
            'governance': {
                'level': badge.level.value,
                'reason': badge.reason
            },
            'sources': ['productive', 'smartsheet'],
            'suggested_actions': self._get_suggested_actions(understanding, data, badge)
        }
    
    def _get_suggested_actions(self, understanding: dict, data: dict, badge) -> list:
        """Suggest next actions based on query results and governance."""
        actions = []
        
        if understanding['intent'] == 'check_availability':
            if data.get('available_hours', 0) > 0:
                actions.append({
                    'label': 'Create booking',
                    'action': 'create_booking',
                    'governance': 'council'  # Requires Council approval
                })
        
        elif understanding['intent'] == 'find_resource':
            if data:
                actions.append({
                    'label': 'View detailed availability',
                    'action': 'show_availability_details'
                })
                actions.append({
                    'label': 'Request allocation',
                    'action': 'request_allocation',
                    'governance': 'council'
                })
        
        return actions
```

---

## PART 3: UI INTEGRATION

### 3.1 SAG Homepage Enhancement

The SAG homepage becomes the Control Room, not a status board.

```html
<!-- templates/index.html - Enhanced SAG Homepage -->

{% extends "base.html" %}

{% block content %}
<div class="control-room">
    
    <!-- HEADER: System State -->
    <header class="system-state">
        <div class="phase-indicator">
            <span class="phase">Phase 3</span>
            <span class="status {{ phase_status }}">{{ phase_status_text }}</span>
        </div>
        
        <div class="cognitive-health">
            <span class="health-indicator {{ cognitive_health.overall }}">
                {{ cognitive_health.overall | upper }}
            </span>
            <div class="health-details">
                <span title="Thermal: {{ cognitive_health.thermal_pressure.avg_temp }}°C">
                    🔥 {{ cognitive_health.thermal_pressure.status }}
                </span>
                <span title="Council confidence: {{ cognitive_health.council_health.avg_confidence }}">
                    🏛️ {{ cognitive_health.council_health.status }}
                </span>
                <span title="Jr tasks: {{ cognitive_health.jr_health.completed_24h }} completed">
                    🤖 {{ cognitive_health.jr_health.status }}
                </span>
            </div>
        </div>
        
        <!-- Pending Approvals Alert -->
        {% if pending_approvals_count > 0 %}
        <div class="pending-alert">
            <a href="/governance/pending">
                ⚠️ {{ pending_approvals_count }} pending approval(s)
            </a>
        </div>
        {% endif %}
    </header>
    
    <!-- MAIN GRID -->
    <div class="control-grid">
        
        <!-- Resource Intelligence Chat -->
        <section class="panel resource-chat">
            <h2>💬 Resource Intelligence</h2>
            <div class="chat-container">
                <div id="chat-messages"></div>
                <form id="chat-form">
                    <input type="text" 
                           id="chat-input" 
                           placeholder="Ask about resources... (e.g., 'Is Bob available for 5 hours?')"
                           autocomplete="off">
                    <button type="submit">Ask</button>
                </form>
            </div>
            <div class="chat-suggestions">
                <button onclick="askQuestion('Who is available this week?')">Available resources</button>
                <button onclick="askQuestion('Show PM allocations')">PM allocations</button>
                <button onclick="askQuestion('Find Python engineer')">Find engineer</button>
            </div>
        </section>
        
        <!-- Governance Panel -->
        <section class="panel governance">
            <h2>🏛️ Governance</h2>
            
            <!-- Active Constraints -->
            <div class="constraints">
                <h3>Active Constraints</h3>
                {% for constraint in active_constraints %}
                <div class="constraint {{ constraint.level }}">
                    <span class="badge">
                        {% if constraint.level == 'locked' %}🔒
                        {% elif constraint.level == 'council' %}⚠️
                        {% elif constraint.level == 'tpm' %}👤
                        {% else %}📋{% endif %}
                    </span>
                    <span class="name">{{ constraint.name }}</span>
                </div>
                {% endfor %}
            </div>
            
            <!-- Pending Changes -->
            <div class="pending-changes">
                <h3>Pending Approvals</h3>
                {% for approval in pending_approvals[:5] %}
                <div class="pending-item">
                    <span class="action">{{ approval.action_type }}</span>
                    <span class="target">{{ approval.target_resource }}</span>
                    <span class="expires">{{ approval.expires_in }}</span>
                    {% if can_approve %}
                    <button onclick="approveChange({{ approval.approval_id }})">Approve</button>
                    {% endif %}
                </div>
                {% endfor %}
                {% if pending_approvals|length > 5 %}
                <a href="/governance/pending">View all ({{ pending_approvals|length }})</a>
                {% endif %}
            </div>
            
            <!-- Authority Quick Reference -->
            <div class="authority-quick">
                <a href="/governance/authority">View Authority Map →</a>
            </div>
        </section>
        
        <!-- Jr Task Dashboard -->
        <section class="panel jr-tasks">
            <h2>🤖 Jr Agents</h2>
            <div class="task-stats">
                <div class="stat">
                    <span class="value">{{ jr_stats.active_agents }}</span>
                    <span class="label">Active</span>
                </div>
                <div class="stat">
                    <span class="value">{{ jr_stats.completed_24h }}</span>
                    <span class="label">Done (24h)</span>
                </div>
                <div class="stat">
                    <span class="value">{{ jr_stats.pending }}</span>
                    <span class="label">Pending</span>
                </div>
            </div>
            <div class="recent-tasks">
                {% for task in recent_tasks[:5] %}
                <div class="task {{ task.status }}">
                    <span class="status-icon">
                        {% if task.status == 'completed' %}🟢
                        {% elif task.status == 'in_progress' %}🟠
                        {% elif task.status == 'assigned' %}🟡
                        {% else %}🔵{% endif %}
                    </span>
                    <span class="task-id">{{ task.task_id }}</span>
                    <span class="agent">{{ task.assigned_to }}</span>
                </div>
                {% endfor %}
            </div>
            <a href="/jr/dashboard">Full Dashboard →</a>
        </section>
        
        <!-- Service Health -->
        <section class="panel services">
            <h2>⚙️ Services</h2>
            {% for service in services %}
            <div class="service {{ service.status }}">
                <span class="status-dot"></span>
                <span class="name">{{ service.name }}</span>
                <span class="endpoint">{{ service.endpoint }}</span>
                {% if service.can_restart %}
                <button class="restart" 
                        onclick="restartService('{{ service.id }}')"
                        title="Restart requires: {{ service.restart_governance }}">
                    🔄
                </button>
                {% endif %}
            </div>
            {% endfor %}
        </section>
        
        <!-- Thermal Memory -->
        <section class="panel thermal">
            <h2>🔥 Hot Memories</h2>
            <div class="memory-list">
                {% for memory in hot_memories[:5] %}
                <div class="memory" style="--temp: {{ memory.temperature_score }}">
                    <span class="temp">{{ memory.temperature_score }}°C</span>
                    <span class="content">{{ memory.content[:80] }}...</span>
                </div>
                {% endfor %}
            </div>
            <a href="/thermal">Browse All →</a>
        </section>
        
    </div>
    
</div>

<script>
// Resource Intelligence Chat
document.getElementById('chat-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = document.getElementById('chat-input');
    const query = input.value.trim();
    if (!query) return;
    
    // Add user message
    addMessage('user', query);
    input.value = '';
    
    // Query the resource intelligence service
    try {
        const response = await fetch('/api/resource/query', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query: query})
        });
        const data = await response.json();
        
        // Add response with governance badge
        addMessage('assistant', data.answer, data.governance);
        
        // Show suggested actions
        if (data.suggested_actions && data.suggested_actions.length > 0) {
            showSuggestions(data.suggested_actions);
        }
    } catch (error) {
        addMessage('system', 'Error processing query: ' + error.message);
    }
});

function addMessage(role, content, governance = null) {
    const messages = document.getElementById('chat-messages');
    const msg = document.createElement('div');
    msg.className = `message ${role}`;
    
    let html = `<span class="content">${content}</span>`;
    if (governance) {
        const badge = {
            'open': '🔓',
            'audit': '📋',
            'tpm': '👤',
            'council': '⚠️',
            'locked': '🔒'
        }[governance.level] || '';
        html += `<span class="governance-badge" title="${governance.reason}">${badge}</span>`;
    }
    
    msg.innerHTML = html;
    messages.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
}

function askQuestion(question) {
    document.getElementById('chat-input').value = question;
    document.getElementById('chat-form').dispatchEvent(new Event('submit'));
}

// Service restart with governance check
async function restartService(serviceId) {
    if (!confirm('Restart service? This action will be logged.')) return;
    
    const response = await fetch(`/api/services/${serviceId}/restart`, {
        method: 'POST'
    });
    
    const data = await response.json();
    
    if (data.requires_approval) {
        alert(`This action requires ${data.approval_level} approval. Request submitted.`);
    } else {
        alert('Service restart initiated.');
        location.reload();
    }
}
</script>
{% endblock %}
```

---

## PART 4: DEPLOYMENT TASKS

### Task Sequence

```sql
-- Announce tasks to Jr system

INSERT INTO jr_task_announcements (task_id, task_type, task_content, priority, required_capabilities, preferred_node)
VALUES
-- Schema tasks (bluefin)
('task-gov-schema-001', 'implementation', 
 'Create pending_approvals table on bluefin. Schema in JR_SAG_GOVERNANCE_ENHANCEMENT.md Part 1.2. Test with INSERT/SELECT.',
 1, ARRAY['sql', 'postgresql'], 'bluefin'),

-- Python libraries (redfin)
('task-gov-badges-001', 'implementation',
 'Create /ganuda/lib/governance_badges.py on redfin. GovernanceChecker class with CONSTRAINTS dict and check_action() method. Per JR_SAG_GOVERNANCE_ENHANCEMENT.md Part 1.1.',
 1, ARRAY['python'], 'redfin'),

('task-gov-health-001', 'implementation',
 'Create /ganuda/lib/cognitive_health.py on redfin. get_cognitive_health_metrics() function querying thermal, memory_links, pheromones, council_votes, jr_task tables. Per Part 1.4.',
 1, ARRAY['python', 'postgresql'], 'redfin'),

('task-productive-client-001', 'implementation',
 'Create /ganuda/lib/productive_client.py on redfin. ProductiveClient class with get_people(), get_person_availability(), find_available_resource(). Per Part 2.2.',
 2, ARRAY['python', 'api'], 'redfin'),

('task-smartsheet-client-001', 'implementation',
 'Create /ganuda/lib/smartsheet_client.py on redfin. SmartsheetClient with paginated API support per Feb 2026 migration. Per Part 2.3.',
 2, ARRAY['python', 'api'], 'redfin'),

('task-resource-service-001', 'implementation',
 'Create /ganuda/services/resource_intelligence.py on redfin. ResourceIntelligenceService combining Productive, Smartsheet, Council, Governance. Per Part 2.4.',
 2, ARRAY['python'], 'redfin'),

-- Gateway endpoints (redfin)
('task-gov-endpoints-001', 'implementation',
 'Add governance endpoints to gateway.py: GET /v1/governance/pending, POST /v1/governance/approve/{id}, GET /v1/governance/constraints, GET /v1/cognitive/health. Per Parts 1.2, 1.4.',
 2, ARRAY['python', 'flask'], 'redfin'),

('task-resource-endpoint-001', 'implementation',
 'Add resource intelligence endpoint to gateway: POST /api/resource/query. Integrate ResourceIntelligenceService. Per Part 2.4.',
 2, ARRAY['python', 'flask'], 'redfin'),

-- UI templates (redfin)
('task-gov-ui-001', 'implementation',
 'Create governance UI templates: authority_map.html, pending_approvals.html. Per Part 1.3.',
 3, ARRAY['html', 'jinja2', 'css'], 'redfin'),

('task-homepage-enhance-001', 'implementation',
 'Enhance SAG homepage (index.html) with Control Room layout: governance panel, resource chat, cognitive health, Jr dashboard. Per Part 3.1.',
 3, ARRAY['html', 'jinja2', 'javascript', 'css'], 'redfin')

RETURNING task_id, status;
```

---

## VALIDATION CHECKLIST

### Governance Surfacing
- [ ] pending_approvals table created
- [ ] GovernanceChecker class deployed
- [ ] Constraint badges visible in UI
- [ ] Pending approvals queue functional
- [ ] Authority map page accessible
- [ ] Cognitive health metrics displayed

### Resource Intelligence
- [ ] ProductiveClient connecting to API
- [ ] SmartsheetClient using new paginated endpoints
- [ ] ResourceIntelligenceService processing queries
- [ ] Chat interface functional
- [ ] Governance badges in chat responses
- [ ] Suggested actions appearing

### Integration
- [ ] Gateway endpoints responding
- [ ] SAG homepage showing Control Room layout
- [ ] Council queries working from resource chat
- [ ] Audit trail capturing all queries

---

## SEVEN GENERATIONS CONSIDERATION

This enhancement embodies the principle:

> "Make the intelligence visible. Make authority explicit. Make governance unavoidable."

The UI will no longer be a passive display. It becomes an active governance surface where:
- Every action shows its authority requirements
- No change happens without explicit approval
- All decisions are traceable for 175 years

The resource intelligence chat is not just a convenience - it demonstrates that AI systems can surface their own governance transparently to users.

For Seven Generations - every query, every approval, every constraint visible to those who come after.

---

*Created: December 23, 2025*
*Council Vote: 659655e7824239fb (82.5% confidence)*
*Priority: P1 - Council Mandated*
