#!/usr/bin/env python3
"""
Cherokee Inter-Triad Communication: Thermal Memory API
Allows triads to share knowledge with temperature-based importance

Uses connection pooling to avoid connection issues.
"""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import Json, RealDictCursor
from enum import Enum
from typing import List, Dict, Optional
import uuid
from datetime import datetime
import os


class AccessLevel(Enum):
    PUBLIC = "public"           # All triads can read
    TRIAD_ONLY = "triad_only"   # Only source triad can read
    SPECIFIC = "specific"        # Only allowed_triads can read
    SACRED = "sacred"            # >75°C, auto-shared to relevant triads


class TriadMemoryAPI:
    """API for inter-triad thermal memory sharing"""

    def __init__(self, db_connection_string: str = None):
        if db_connection_string is None:
            # Default: PostgreSQL on bluefin (192.168.132.222)
            db_connection_string = "postgresql://claude:{os.environ.get('CHEROKEE_DB_PASS', '')}@192.168.132.222:5432/triad_federation"

        # Use connection pooling to handle connections properly
        self.connection_pool = psycopg2.pool.SimpleConnectionPool(
            1,  # minconn
            10,  # maxconn
            db_connection_string
        )

        if self.connection_pool:
            print("Connection pool created successfully")

        self._ensure_schema()

    def _get_connection(self):
        """Get a connection from the pool"""
        return self.connection_pool.getconn()

    def _put_connection(self, conn):
        """Return a connection to the pool"""
        self.connection_pool.putconn(conn)

    def _ensure_schema(self):
        """Create table if not exists"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS triad_shared_memories (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    content TEXT NOT NULL,
                    temperature FLOAT NOT NULL CHECK (temperature >= 0 AND temperature <= 100),
                    source_triad VARCHAR(255) NOT NULL,
                    tags TEXT[] DEFAULT '{}',
                    access_level VARCHAR(50) DEFAULT 'public',
                    allowed_triads TEXT[] DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_triad_memories_temp
                    ON triad_shared_memories(temperature DESC);
                CREATE INDEX IF NOT EXISTS idx_triad_memories_source
                    ON triad_shared_memories(source_triad);
                CREATE INDEX IF NOT EXISTS idx_triad_memories_tags
                    ON triad_shared_memories USING GIN(tags);
            """)
            conn.commit()
            cursor.close()
        finally:
            self._put_connection(conn)

    def write_memory(
        self,
        content: str,
        temperature: float,
        source_triad: str,
        tags: List[str] = None,
        access_level: AccessLevel = AccessLevel.PUBLIC,
        allowed_triads: List[str] = None
    ) -> str:
        """
        Write a memory to the shared thermal memory.

        Returns: UUID of created memory
        """
        if tags is None:
            tags = []
        if allowed_triads is None:
            allowed_triads = []

        # Three Chiefs guidance: >75°C = sacred (auto-share)
        if temperature >= 75.0:
            access_level = AccessLevel.SACRED
            print(f"🔥 SACRED MEMORY: {temperature}°C - Auto-sharing to federation")

        memory_id = str(uuid.uuid4())

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO triad_shared_memories
                (id, content, temperature, source_triad, tags, access_level, allowed_triads)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                memory_id,
                content,
                temperature,
                source_triad,
                tags,
                access_level.value,
                allowed_triads
            ))
            conn.commit()
            cursor.close()

            # If sacred, publish event to message queue
            if temperature >= 75.0:
                self._publish_sacred_memory_event(memory_id, content, source_triad, temperature)

        finally:
            self._put_connection(conn)

        return memory_id

    def query_memories(
        self,
        requesting_triad: str,
        min_temperature: float = 0.0,
        max_temperature: float = 100.0,
        tags: List[str] = None,
        source_triad: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Query thermal memories with access control enforcement.
        """
        query = """
            SELECT * FROM triad_shared_memories
            WHERE temperature >= %s AND temperature <= %s
        """
        params = [min_temperature, max_temperature]

        # Tag filtering
        if tags:
            query += " AND tags && %s"
            params.append(tags)

        # Source filtering
        if source_triad:
            query += " AND source_triad = %s"
            params.append(source_triad)

        # Access control
        query += """
            AND (
                access_level = 'public'
                OR access_level = 'sacred'
                OR source_triad = %s
                OR %s = ANY(allowed_triads)
            )
        """
        params.extend([requesting_triad, requesting_triad])

        query += " ORDER BY temperature DESC, created_at DESC LIMIT %s"
        params.append(limit)

        conn = self._get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            return results
        finally:
            self._put_connection(conn)

    def get_sacred_memories(self, requesting_triad: str) -> List[Dict]:
        """Get all sacred memories (>75°C)"""
        return self.query_memories(
            requesting_triad=requesting_triad,
            min_temperature=75.0
        )

    def _publish_sacred_memory_event(self, memory_id, content, source_triad, temperature):
        """Publish sacred memory to message queue"""
        # This will be implemented in Phase 2 (Message Queue)
        # For now, just log
        print(f"🔥 SACRED MEMORY EVENT: {source_triad} shared {temperature}°C memory")
        print(f"   Memory ID: {memory_id}")
        print(f"   Preview: {content[:200]}...")

    def close(self):
        """Close all connections in the pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            print("All connections closed")


# Example usage and testing
if __name__ == "__main__":
    api = TriadMemoryAPI()

    # Medicine Woman shares solar flare warning
    memory_id = api.write_memory(
        content="Solar flare detected: X-class, peak flux 2850 sfu. Historical correlation: 87% BTC pump within 48 hours during solar maximum. Recommend Financial Triad adjust volatility expectations.",
        temperature=95.0,  # SACRED - auto-shares
        source_triad="medicine_woman_triad",
        tags=["solar", "trading", "volatility", "X-class"],
        access_level=AccessLevel.SACRED
    )
    print(f"✅ Medicine Woman wrote sacred memory: {memory_id}")

    # Financial Triad queries for relevant memories
    relevant_memories = api.query_memories(
        requesting_triad="financial_triad",
        min_temperature=70.0,
        tags=["trading", "volatility"]
    )
    print(f"✅ Financial Triad found {len(relevant_memories)} relevant memories")

    for mem in relevant_memories:
        print(f"\n🔥 {mem['temperature']}°C from {mem['source_triad']}")
        print(f"   {mem['content'][:200]}...")

    api.close()
