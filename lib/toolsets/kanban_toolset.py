"""KanbanToolSet — search and query Jr tasks / kanban tickets.

Read tools: search_tasks, get_overdue_tasks, get_task_stats
Council vote #798ad0b799bad552 (ToolSet pattern).
"""

from .base import ToolSet, ToolDescriptor, get_db_connection


class KanbanToolSet(ToolSet):
    domain = "kanban"

    def get_tools(self) -> list:
        return [
            ToolDescriptor(
                name="search_tasks",
                description="Search Jr tasks by title, status, or priority. Returns matching tasks with id, title, status, priority, creation date.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Text to search in task title/description"},
                        "status": {"type": "string", "description": "Filter by status: pending, completed, cancelled"},
                        "priority": {"type": "integer", "description": "Filter by priority number (1=highest)"},
                        "limit": {"type": "integer", "description": "Max results (default 10)"},
                    },
                },
                safety_class="read",
            ),
            ToolDescriptor(
                name="get_overdue_tasks",
                description="Get tasks that have been pending for more than 7 days without completion.",
                parameters={"type": "object", "properties": {}},
                safety_class="read",
            ),
            ToolDescriptor(
                name="get_task_stats",
                description="Get task statistics: total, by status, by priority, completion rate.",
                parameters={"type": "object", "properties": {}},
                safety_class="read",
            ),
        ]

    def search_tasks(self, query: str = "", status: str = "",
                     priority: int = 0, limit: int = 10) -> dict:
        """Search jr_work_queue."""
        conn = get_db_connection()
        cur = conn.cursor()

        conditions = []
        params = []

        if query:
            conditions.append("(title ILIKE %s OR description ILIKE %s)")
            params.extend([f"%{query}%", f"%{query}%"])
        if status:
            conditions.append("status = %s")
            params.append(status)
        if priority:
            conditions.append("priority = %s")
            params.append(priority)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        cur.execute(f"""
            SELECT id, title, status, priority, task_id, created_at
            FROM jr_work_queue
            {where}
            ORDER BY created_at DESC
            LIMIT %s
        """, params + [limit])

        rows = cur.fetchall()
        cur.close()
        conn.close()

        return {
            "count": len(rows),
            "tasks": [
                {
                    "id": r[0],
                    "title": r[1],
                    "status": r[2],
                    "priority": r[3],
                    "task_id": r[4],
                    "created": str(r[5]),
                }
                for r in rows
            ],
        }

    def get_overdue_tasks(self) -> dict:
        """Get tasks pending > 7 days."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, status, priority, created_at
            FROM jr_work_queue
            WHERE status = 'pending'
            AND created_at < NOW() - INTERVAL '7 days'
            ORDER BY created_at ASC
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        return {
            "overdue_count": len(rows),
            "tasks": [
                {
                    "id": r[0],
                    "title": r[1],
                    "status": r[2],
                    "priority": r[3],
                    "created": str(r[4]),
                }
                for r in rows
            ],
        }

    def get_task_stats(self) -> dict:
        """Aggregate task statistics."""
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT status, COUNT(*) FROM jr_work_queue GROUP BY status")
        by_status = {r[0]: r[1] for r in cur.fetchall()}

        cur.execute("SELECT priority, COUNT(*) FROM jr_work_queue GROUP BY priority")
        by_priority = {str(r[0]): r[1] for r in cur.fetchall()}

        total = sum(by_status.values())
        done = by_status.get("completed", 0)

        cur.close()
        conn.close()

        return {
            "total": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "completion_rate": round(done / total * 100, 1) if total > 0 else 0,
        }
