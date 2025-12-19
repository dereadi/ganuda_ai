# Add method to TribeInterface
def create_ticket(self, title: str, description: str, priority: int = 2,
                  assigned_jr: str = None, requester: str = "telegram") -> dict:
    """Create a ticket in Jr work queue"""
    try:
        with self.get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO jr_work_queue (
                    task_id, title, description, assigned_jr,
                    priority, status, requester, created_at
                ) VALUES (
                    md5(%s || %s),
                    %s, %s, %s, %s, 'pending', %s, NOW()
                ) RETURNING task_id, title
            """, (
                title, str(datetime.now()),
                title, description, assigned_jr, priority, requester
            ))
            result = cur.fetchone()
            conn.commit()
            return {"success": True, "task_id": result[0], "title": result[1]}
    except Exception as e:
        return {"error": str(e)}