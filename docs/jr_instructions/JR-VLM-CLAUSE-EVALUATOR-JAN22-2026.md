# Jr Task: VLM Clause Evaluator

Evaluate thermal_clauses against new relationships and trigger escalations.

**Assigned to:** Software Engineer Jr.
**Node:** bluefin (192.168.132.222)
**Priority:** High
**Depends on:** Relationship Storer

## Objective

Create `/ganuda/lib/vlm_clause_evaluator.py` that:
1. Evaluates clauses when new relationships are stored
2. Triggers actions when conditions are met
3. Escalates to redfin brain for complex decisions

## Implementation

**File:** `/ganuda/lib/vlm_clause_evaluator.py`

```python
"""
Cherokee AI Federation - VLM Clause Evaluator
Evaluates IF-THEN rules and escalates to redfin brain when needed
"""

import psycopg2
import httpx
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": "192.168.132.222",
    "database": "zammad_production",
    "user": "claude",
    "password": "jawaseatlasers2"
}

GATEWAY_URL = "http://192.168.132.223:8080"
API_KEY = "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"

@dataclass
class ClauseEvaluation:
    """Result of evaluating a clause"""
    clause_id: int
    clause_name: str
    result: bool
    triggered_relationships: List[int]
    action: str  # none, alert, escalate, log
    escalation_reason: Optional[str]


@dataclass
class EscalationRequest:
    """Request to send to redfin brain"""
    reason: str
    clause_id: int
    relationships: List[Dict]
    context: Dict
    priority: str  # low, medium, high, sacred_fire


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def get_active_clauses(conn) -> List[Dict]:
    """Get all active IF-THEN clauses."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, name, description, condition_relationship_ids, 
                   action_relationship_ids, priority, metadata
            FROM active_thermal_clauses
            WHERE clause_type = 'if_then'
            ORDER BY priority ASC
        """)
        columns = ['id', 'name', 'description', 'condition_ids', 'action_ids', 'priority', 'metadata']
        return [dict(zip(columns, row)) for row in cur.fetchall()]


def check_relationships_active(conn, relationship_ids: List[int]) -> bool:
    """Check if all specified relationships are currently active."""
    if not relationship_ids:
        return True
        
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM active_thermal_relationships
            WHERE id = ANY(%s)
        """, (relationship_ids,))
        count = cur.fetchone()[0]
        return count == len(relationship_ids)


def get_relationship_details(conn, relationship_ids: List[int]) -> List[Dict]:
    """Get details of relationships for escalation context."""
    if not relationship_ids:
        return []
        
    with conn.cursor() as cur:
        cur.execute("""
            SELECT r.id, r.relationship_type, r.confidence, r.provenance,
                   sm.original_content as source_content,
                   tm.original_content as target_content
            FROM thermal_relationships r
            LEFT JOIN thermal_memory_archive sm ON r.source_memory_id = sm.id
            LEFT JOIN thermal_memory_archive tm ON r.target_memory_id = tm.id
            WHERE r.id = ANY(%s)
        """, (relationship_ids,))
        columns = ['id', 'type', 'confidence', 'provenance', 'source', 'target']
        return [dict(zip(columns, row)) for row in cur.fetchall()]


def update_clause_evaluation(conn, clause_id: int, result: bool, context: Dict):
    """Update clause evaluation state."""
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE thermal_clauses 
            SET last_evaluated = NOW(),
                evaluation_result = %s,
                evaluation_context = %s
            WHERE id = %s
        """, (result, json.dumps(context), clause_id))


def escalate_to_redfin(request: EscalationRequest) -> Dict:
    """
    Escalate to redfin brain for higher reasoning.
    This is like sending visual signals to higher cortical areas.
    """
    prompt = f"""VISUAL CORTEX ESCALATION - Requires Higher Reasoning

Reason: {request.reason}
Clause ID: {request.clause_id}
Priority: {request.priority}

Detected Relationships:
{json.dumps(request.relationships, indent=2)}

Context:
{json.dumps(request.context, indent=2)}

As the higher cortical processing center, analyze this visual detection and determine:
1. Is this a genuine security concern or false positive?
2. What action should be taken?
3. Should this trigger an alert?
4. Any patterns with recent detections?

Respond with JSON: {{"assessment": "...", "action": "none|log|alert|urgent", "reasoning": "..."}}"""

    try:
        response = httpx.post(
            f"{GATEWAY_URL}/v1/chat/completions",
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            json={
                "messages": [
                    {"role": "system", "content": "You are the higher reasoning center of the Cherokee AI Federation. Analyze escalated visual detections and determine appropriate responses."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 300,
                "temperature": 0.3
            },
            timeout=30.0
        )
        
        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Parse JSON response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        return json.loads(content.strip())
        
    except Exception as e:
        logger.error(f"Escalation failed: {e}")
        return {"assessment": "escalation_failed", "action": "log", "reasoning": str(e)}


def evaluate_clauses_for_relationships(new_relationship_ids: List[int]) -> List[ClauseEvaluation]:
    """
    Evaluate all clauses that might be triggered by new relationships.
    
    Args:
        new_relationship_ids: IDs of newly created relationships
        
    Returns:
        List of clause evaluations
    """
    results = []
    conn = get_db_connection()
    
    try:
        clauses = get_active_clauses(conn)
        
        for clause in clauses:
            # Check if any new relationships are in this clause's conditions
            condition_ids = clause.get('condition_ids') or []
            relevant = any(rid in condition_ids for rid in new_relationship_ids)
            
            if not relevant and condition_ids:
                continue  # Skip clauses not related to new relationships
                
            # Evaluate clause
            conditions_met = check_relationships_active(conn, condition_ids)
            
            # Determine action
            action = "none"
            escalation_reason = None
            
            if conditions_met:
                metadata = clause.get('metadata') or {}
                
                # Check if escalation needed
                if metadata.get('escalate_on_trigger', False):
                    action = "escalate"
                    escalation_reason = f"Clause '{clause['name']}' triggered"
                elif clause['priority'] <= 2:  # High priority
                    action = "alert"
                else:
                    action = "log"
                    
            # Update clause state
            update_clause_evaluation(conn, clause['id'], conditions_met, {
                "triggered_by": new_relationship_ids,
                "evaluated_at": datetime.now().isoformat()
            })
            
            eval_result = ClauseEvaluation(
                clause_id=clause['id'],
                clause_name=clause['name'] or f"Clause_{clause['id']}",
                result=conditions_met,
                triggered_relationships=new_relationship_ids if conditions_met else [],
                action=action,
                escalation_reason=escalation_reason
            )
            
            # Handle escalation
            if action == "escalate" and escalation_reason:
                rel_details = get_relationship_details(conn, new_relationship_ids)
                escalation = EscalationRequest(
                    reason=escalation_reason,
                    clause_id=clause['id'],
                    relationships=rel_details,
                    context={"clause_name": clause['name'], "description": clause['description']},
                    priority="high" if clause['priority'] <= 2 else "medium"
                )
                brain_response = escalate_to_redfin(escalation)
                logger.info(f"Redfin brain response: {brain_response}")
            
            results.append(eval_result)
            
        conn.commit()
        
    finally:
        conn.close()
        
    return results


if __name__ == "__main__":
    # Test evaluation
    print("Testing clause evaluation...")
    results = evaluate_clauses_for_relationships([1, 2])
    for r in results:
        print(f"Clause '{r.clause_name}': {r.result} -> {r.action}")
```

## Verification

```bash
cd /ganuda/lib
python3 vlm_clause_evaluator.py
```

## Success Criteria

1. Evaluates clauses against relationships
2. Determines appropriate action (none/log/alert/escalate)
3. Escalates to redfin brain when needed
4. Updates clause evaluation state in database
