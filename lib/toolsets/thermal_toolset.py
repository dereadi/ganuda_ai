"""ThermalToolSet — search, stats, and summarize thermal memories.

Read tools: search_thermals, get_thermal_stats, summarize_topic
Write tools: create_thermal (requires council gate)

Council votes #798ad0b7 (ToolSet pattern) + #4df2e34784f1b36c (MyBrain adoption).
"""

import json
import requests
from .base import ToolSet, ToolDescriptor, get_db_connection


class ThermalToolSet(ToolSet):
    domain = "thermal"

    def get_tools(self) -> list:
        return [
            ToolDescriptor(
                name="search_thermals",
                description="Search thermal memories by content, domain_tag, or temperature range. Returns matching thermals with id, content snippet, temperature, domain, timestamp.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Text to search in thermal content"},
                        "domain_tag": {"type": "string", "description": "Filter by domain (infrastructure, architecture, governance, milestone, etc.)"},
                        "min_temp": {"type": "integer", "description": "Minimum temperature score (0-100)"},
                        "max_temp": {"type": "integer", "description": "Maximum temperature score (0-100)"},
                        "sacred_only": {"type": "boolean", "description": "Only return sacred thermals"},
                        "limit": {"type": "integer", "description": "Max results (default 10)"},
                    },
                },
                safety_class="read",
            ),
            ToolDescriptor(
                name="get_thermal_stats",
                description="Get thermal memory statistics: total count, count by domain, average temperature, sacred count.",
                parameters={"type": "object", "properties": {}},
                safety_class="read",
            ),
            ToolDescriptor(
                name="summarize_topic",
                description="Search thermals semantically for a topic and generate a consolidated summary. Use when asked 'what do we know about X' or 'summarize our knowledge on X'.",
                parameters={
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "The topic to search and summarize"},
                        "top_k": {"type": "integer", "description": "Number of thermal chunks to retrieve (default 10)"},
                        "domain_filter": {"type": "string", "description": "Optional domain_tag filter"},
                    },
                    "required": ["topic"],
                },
                safety_class="read",
            ),
            ToolDescriptor(
                name="create_thermal",
                description="Create a new thermal memory. WRITE — requires council approval.",
                parameters={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "The thermal memory content"},
                        "temperature": {"type": "integer", "description": "Temperature score 0-100"},
                        "domain_tag": {"type": "string", "description": "Domain tag"},
                        "sacred": {"type": "boolean", "description": "Whether this is a sacred pattern"},
                    },
                    "required": ["content", "temperature", "domain_tag"],
                },
                safety_class="write",
            ),
        ]

    def search_thermals(self, query: str = "", domain_tag: str = "",
                        min_temp: int = 0, max_temp: int = 100,
                        sacred_only: bool = False, limit: int = 10) -> dict:
        """Search thermal_memory_archive."""
        conn = get_db_connection()
        cur = conn.cursor()

        conditions = ["temperature_score BETWEEN %s AND %s"]
        params = [min_temp, max_temp]

        if query:
            conditions.append("original_content ILIKE %s")
            params.append(f"%{query}%")
        if domain_tag:
            conditions.append("domain_tag = %s")
            params.append(domain_tag)
        if sacred_only:
            conditions.append("sacred_pattern = true")

        where = " AND ".join(conditions)
        cur.execute(f"""
            SELECT id, LEFT(original_content, 200), temperature_score,
                   domain_tag, sacred_pattern, created_at
            FROM thermal_memory_archive
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT %s
        """, params + [limit])

        rows = cur.fetchall()
        cur.close()
        conn.close()

        return {
            "count": len(rows),
            "thermals": [
                {
                    "id": r[0],
                    "content_snippet": r[1],
                    "temperature": r[2],
                    "domain": r[3],
                    "sacred": r[4],
                    "created_at": str(r[5]),
                }
                for r in rows
            ],
        }

    def get_thermal_stats(self) -> dict:
        """Get aggregate thermal stats."""
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT COUNT(*),
                   AVG(temperature_score),
                   COUNT(*) FILTER (WHERE sacred_pattern)
            FROM thermal_memory_archive
        """)
        total, avg_temp, sacred = cur.fetchone()

        cur.execute("""
            SELECT domain_tag, COUNT(*)
            FROM thermal_memory_archive
            GROUP BY domain_tag
            ORDER BY COUNT(*) DESC
            LIMIT 15
        """)
        domains = {r[0]: r[1] for r in cur.fetchall()}

        cur.close()
        conn.close()

        return {
            "total": total,
            "avg_temperature": round(float(avg_temp), 1) if avg_temp else 0,
            "sacred_count": sacred,
            "by_domain": domains,
        }

    def summarize_topic(self, topic: str, top_k: int = 10,
                        domain_filter: str = "") -> dict:
        """Semantic search thermals for topic, feed to LLM for synthesis.

        Adapted from jsdorn/MyBrain summarize_topic MCP tool.
        Council vote #4df2e34784f1b36c.
        """
        conn = get_db_connection()
        cur = conn.cursor()

        # Step 1: Try semantic search via embedding
        # Fall back to text search if embeddings unavailable
        use_vector = False
        try:
            embed_resp = requests.post(
                "http://192.168.132.224:8003/embed",
                json={"text": topic},
                timeout=5,
            )
            if embed_resp.status_code == 200:
                query_vector = embed_resp.json().get("embedding")
                if query_vector:
                    use_vector = True
        except Exception:
            pass

        if use_vector:
            # Vector search
            domain_clause = "AND domain_tag = %s" if domain_filter else ""
            params = [str(query_vector)]
            if domain_filter:
                params.append(domain_filter)
            params.append(str(query_vector))
            params.append(top_k)

            cur.execute(f"""
                SELECT id, LEFT(original_content, 500), temperature_score,
                       domain_tag, sacred_pattern,
                       embedding <=> %s::vector AS distance
                FROM thermal_memory_archive
                WHERE embedding IS NOT NULL
                {domain_clause}
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, params)
        else:
            # Fallback: text search
            domain_clause = "AND domain_tag = %s" if domain_filter else ""
            params = [f"%{topic}%"]
            if domain_filter:
                params.append(domain_filter)
            params.append(top_k)

            cur.execute(f"""
                SELECT id, LEFT(original_content, 500), temperature_score,
                       domain_tag, sacred_pattern, 0.0 AS distance
                FROM thermal_memory_archive
                WHERE original_content ILIKE %s
                {domain_clause}
                ORDER BY temperature_score DESC
                LIMIT %s
            """, params)

        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            return {
                "topic": topic,
                "chunks_found": 0,
                "summary": f"No thermals found related to '{topic}'.",
            }

        # Step 2: Build context from retrieved chunks
        context_texts = []
        for row in rows:
            tid, content, temp, domain, sacred, dist = row
            prefix = "[SACRED] " if sacred else ""
            context_texts.append(f"{prefix}[{domain}, temp={temp}]: {content}")

        context_block = "\n\n---\n\n".join(context_texts)

        # Step 3: Feed to vLLM for synthesis
        try:
            synth_resp = requests.post(
                "http://localhost:8000/v1/chat/completions",
                json={
                    "model": "/ganuda/models/qwen2.5-72b-instruct-awq",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a knowledge synthesizer for the Cherokee AI Federation. "
                                "Given thermal memory fragments on a topic, produce a concise, accurate summary. "
                                "Cite specific details from the fragments. Flag any contradictions."
                            ),
                        },
                        {
                            "role": "user",
                            "content": f"Summarize what we know about: {topic}\n\nThermal fragments:\n{context_block}",
                        },
                    ],
                    "max_tokens": 600,
                    "temperature": 0.3,
                },
                timeout=120,
            )
            synth_resp.raise_for_status()
            summary = synth_resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            # If LLM unavailable, return raw fragments
            summary = f"[LLM synthesis unavailable: {e}]\n\nRaw fragments:\n" + "\n".join(
                ct[:200] for ct in context_texts[:5]
            )

        return {
            "topic": topic,
            "chunks_found": len(rows),
            "domains": list(set(r[3] for r in rows)),
            "sacred_count": sum(1 for r in rows if r[4]),
            "search_method": "vector" if use_vector else "text",
            "summary": summary,
        }

    def create_thermal(self, content: str, temperature: int,
                       domain_tag: str, sacred: bool = False) -> dict:
        """Create thermal. WRITE — council gate required by caller."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (original_content, temperature_score, domain_tag, sacred_pattern, memory_hash)
            VALUES (%s, %s, %s, %s, encode(sha256((%s || NOW()::text)::bytea), 'hex'))
            RETURNING id
        """, (content, temperature, domain_tag, sacred, f"toolset-{domain_tag}-"))

        thermal_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return {"created_id": thermal_id, "temperature": temperature, "domain": domain_tag}
