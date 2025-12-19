#\!/usr/bin/env python3
"""Add temporal context detection to gateway"""

with open("/ganuda/services/llm_gateway/gateway.py", "r") as f:
    content = f.read()

# New temporal detection functions
temporal_functions = """

# Temporal Context Detection for Council Memory
def detect_temporal_query(question: str):
    \"\"\"Detect if question is about recent events and extract timeframe\"\"\"
    import re
    from datetime import timedelta
    
    question_lower = question.lower()
    
    temporal_keywords = [
        "today", "yesterday", "this morning", "tonight",
        "recent", "recently", "latest", "last",
        "what did we", "what have we", "what was",
        "built", "deployed", "created", "implemented",
        "changes", "updates", "enhancements", "progress",
        "done", "accomplished", "completed"
    ]
    
    is_temporal = any(kw in question_lower for kw in temporal_keywords)
    
    if not is_temporal:
        return False, None
    
    if "today" in question_lower or "this morning" in question_lower:
        return True, timedelta(hours=24)
    elif "yesterday" in question_lower:
        return True, timedelta(hours=48)
    elif "this week" in question_lower:
        return True, timedelta(days=7)
    
    match = re.search(r"last\\s+(\\d+)\\s+(hour|day|week)", question_lower)
    if match:
        num = int(match.group(1))
        unit = match.group(2)
        if unit == "hour":
            return True, timedelta(hours=num)
        elif unit == "day":
            return True, timedelta(days=num)
        elif unit == "week":
            return True, timedelta(weeks=num)
    
    return True, timedelta(hours=48)


def get_temporal_context(timeframe) -> str:
    \"\"\"Query thermal memory for recent events\"\"\"
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(\"\"\"
                SELECT LEFT(original_content, 300), created_at, temperature_score
                FROM thermal_memory_archive
                WHERE created_at > NOW() - %s
                  AND original_content NOT LIKE 'ALERT%%'
                  AND original_content NOT LIKE 'TPM %%'
                ORDER BY temperature_score DESC, created_at DESC
                LIMIT 10
            \"\"\", (timeframe,))
            rows = cur.fetchall()
        
        if not rows:
            return ""
        
        hours = int(timeframe.total_seconds() / 3600)
        context_lines = [f"\\n[RECENT TRIBAL MEMORY - Last {hours} hours]:"]
        for content, created, temp in rows:
            date_str = created.strftime("%b %d %H:%M")
            summary = content.replace("\\n", " ")[:200]
            context_lines.append(f"- [{date_str}] {summary}")
        
        context_lines.append("\\nBased on this context, answer the question.\\n")
        return "\\n".join(context_lines)
    except Exception as e:
        print(f"[TEMPORAL] Error: {e}")
        return ""

"""

# Find insertion point - after SPECIALISTS dict
marker = "# 7 Specialist definitions"
if marker in content:
    idx = content.find(marker)
    content = content[:idx] + temporal_functions + "\n" + content[idx:]
    print("SUCCESS: Added temporal functions")
else:
    # Alternative: add before @app.get("/health")
    marker2 = "@app.get(\"/health\")"
    if marker2 in content:
        idx = content.find(marker2)
        content = content[:idx] + temporal_functions + "\n" + content[idx:]
        print("SUCCESS: Added temporal functions before /health")
    else:
        print("ERROR: Could not find insertion point")

with open("/ganuda/services/llm_gateway/gateway.py", "w") as f:
    f.write(content)
