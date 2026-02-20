"""
Cherokee AI Federation - VLM Clause Evaluator
Evaluates IF-THEN rules and escalates to redfin brain when needed
"""

import psycopg2
import httpx
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from lib.secrets_loader import get_db_config
DB_CONFIG = get_db_config()
GATEWAY_URL = "http://192.168.132.223:8080"
API_KEY = "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"

@dataclass
class ClauseEvaluation:
    clause_id: int
    clause_name: str
    result: bool
    triggered_relationships: List[int]
    action: str
    escalation_reason: Optional[str]

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_active_clauses(conn) -> List[Dict]:
    with conn.cursor() as cur:
        cur.execute("""SELECT id, name, description, condition_relationship_ids, action_relationship_ids, priority, metadata
            FROM active_thermal_clauses WHERE clause_type = 'if_then' ORDER BY priority ASC""")
        return [dict(zip(['id', 'name', 'description', 'condition_ids', 'action_ids', 'priority', 'metadata'], row)) for row in cur.fetchall()]

def check_relationships_active(conn, relationship_ids: List[int]) -> bool:
    if not relationship_ids: return True
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM active_thermal_relationships WHERE id = ANY(%s)", (relationship_ids,))
        return cur.fetchone()[0] == len(relationship_ids)

def get_relationship_details(conn, relationship_ids: List[int]) -> List[Dict]:
    if not relationship_ids: return []
    with conn.cursor() as cur:
        cur.execute("""SELECT r.id, r.relationship_type, r.confidence, r.provenance, sm.original_content, tm.original_content
            FROM thermal_relationships r
            LEFT JOIN thermal_memory_archive sm ON r.source_memory_id = sm.id
            LEFT JOIN thermal_memory_archive tm ON r.target_memory_id = tm.id WHERE r.id = ANY(%s)""", (relationship_ids,))
        return [dict(zip(['id', 'type', 'confidence', 'provenance', 'source', 'target'], row)) for row in cur.fetchall()]

def escalate_to_redfin(reason: str, clause_id: int, relationships: List[Dict], priority: str) -> Dict:
    prompt = f"""VISUAL CORTEX ESCALATION
Reason: {reason}
Relationships: {json.dumps(relationships, indent=2)}
Analyze and respond with JSON: {{"assessment": "...", "action": "none|log|alert|urgent", "reasoning": "..."}}"""
    try:
        response = httpx.post(f"{GATEWAY_URL}/v1/chat/completions", headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            json={"messages": [{"role": "system", "content": "You are the Cherokee AI higher reasoning center."}, {"role": "user", "content": prompt}], "max_tokens": 300, "temperature": 0.3}, timeout=30.0)
        content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "{}")
        if "```" in content: content = content.split("```")[1].split("```")[0].replace("json", "")
        return json.loads(content.strip())
    except Exception as e:
        return {"assessment": "error", "action": "log", "reasoning": str(e)}

def evaluate_clauses_for_relationships(new_relationship_ids: List[int]) -> List[ClauseEvaluation]:
    results = []
    conn = get_db_connection()
    try:
        for clause in get_active_clauses(conn):
            condition_ids = clause.get('condition_ids') or []
            if condition_ids and not any(rid in condition_ids for rid in new_relationship_ids): continue
            
            conditions_met = check_relationships_active(conn, condition_ids)
            action, escalation_reason = "none", None
            
            if conditions_met:
                metadata = clause.get('metadata') or {}
                if metadata.get('escalate_on_trigger'): action, escalation_reason = "escalate", f"Clause '{clause['name']}' triggered"
                elif clause['priority'] <= 2: action = "alert"
                else: action = "log"
            
            with conn.cursor() as cur:
                cur.execute("UPDATE thermal_clauses SET last_evaluated = NOW(), evaluation_result = %s WHERE id = %s", (conditions_met, clause['id']))
            
            if action == "escalate":
                escalate_to_redfin(escalation_reason, clause['id'], get_relationship_details(conn, new_relationship_ids), "high")
            
            results.append(ClauseEvaluation(clause['id'], clause['name'] or f"Clause_{clause['id']}", conditions_met, new_relationship_ids if conditions_met else [], action, escalation_reason))
        conn.commit()
    finally:
        conn.close()
    return results

if __name__ == "__main__":
    results = evaluate_clauses_for_relationships([1])
    for r in results: print(f"Clause '{r.clause_name}': {r.result} -> {r.action}")
