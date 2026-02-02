def seed_memory(self, content: str, memory_type: str = "telegram_interaction",
                temperature: int = 70, tags: list = None) -> dict:
    """Write to thermal memory archive with SHA-256 integrity checksum."""
    try:
        import hashlib as _hl
        content_checksum = _hl.sha256(content.encode('utf-8', errors='replace')).hexdigest()

        with self.get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO thermal_memory_archive (
                    memory_hash, original_content, current_stage,
                    temperature_score, sacred_pattern, metadata,
                    time_sense, content_checksum, created_at
                ) VALUES (
                    md5(%s || %s),
                    %s,
                    CASE WHEN %s > 80 THEN 'HOT' WHEN %s > 50 THEN 'WARM' ELSE 'COOL' END,
                    %s,
                    false,
                    %s,
                    'SEVEN_GENERATIONS',
                    %s,
                    NOW()
                ) RETURNING id
            """, (
                content, str(datetime.now()),
                content,
                temperature, temperature,
                temperature,
                json.dumps({"type": memory_type, "source": "telegram_chief", "tags": tags or []}),
                content_checksum
            ))
            memory_id = cur.fetchone()[0]
            conn.commit()
            return {"success": True, "memory_id": memory_id}
    except Exception as e:
        return {"error": str(e)}