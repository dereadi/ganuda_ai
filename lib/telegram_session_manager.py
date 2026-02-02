#!/usr/bin/env python3
"""
Telegram Session Manager for Cherokee AI Federation
Provides persistent conversation context for the Telegram Chief Bot.

Uses the telegram_sessions table for storage.
"""

import psycopg2
import psycopg2.extras
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

# Session configuration
MAX_HISTORY_MESSAGES = 10
SESSION_EXPIRY_HOURS = 24
MAX_CONTEXT_LENGTH = 2000


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


class TelegramSessionManager:
    """
    Manages conversation sessions for Telegram users.

    Features:
    - Persistent conversation history
    - Automatic session expiry
    - Context compression for LLM prompts
    - Thermal memory integration
    """

    def __init__(self, user_id: int, chat_id: int, username: str = None):
        self.user_id = user_id
        self.chat_id = chat_id
        self.username = username
        self.session_id = None
        self._ensure_session()

    def _ensure_session(self) -> None:
        """Get or create a session for this user/chat."""
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Look for active session
                cur.execute("""
                    SELECT session_id, context, created_at, last_active
                    FROM telegram_sessions
                    WHERE user_id = %s AND chat_id = %s AND expires_at > NOW()
                    ORDER BY last_active DESC
                    LIMIT 1
                """, (self.user_id, self.chat_id))

                row = cur.fetchone()

                if row:
                    self.session_id = row['session_id']
                    # Update last_active
                    cur.execute("""
                        UPDATE telegram_sessions
                        SET last_active = NOW(), username = COALESCE(%s, username)
                        WHERE session_id = %s
                    """, (self.username, self.session_id))
                else:
                    # Create new session
                    cur.execute("""
                        INSERT INTO telegram_sessions (user_id, chat_id, username, context)
                        VALUES (%s, %s, %s, %s)
                        RETURNING session_id
                    """, (self.user_id, self.chat_id, self.username, json.dumps({
                        'messages': [],
                        'summary': '',
                        'topics': [],
                        'last_specialist': None
                    })))
                    self.session_id = cur.fetchone()[0]

                conn.commit()
        finally:
            conn.close()

    def get_context(self) -> Dict[str, Any]:
        """Get the current session context."""
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT context FROM telegram_sessions WHERE session_id = %s
                """, (self.session_id,))
                row = cur.fetchone()
                if row and row['context']:
                    return row['context']
                return {'messages': [], 'summary': '', 'topics': [], 'last_specialist': None}
        finally:
            conn.close()

    def add_message(self, role: str, content: str,
                    specialist: str = None, audit_hash: str = None) -> None:
        """
        Add a message to the conversation history.

        Args:
            role: 'user' or 'assistant'
            content: The message content
            specialist: Which specialist responded (if assistant)
            audit_hash: Council vote audit hash (if applicable)
        """
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get current context
                cur.execute("""
                    SELECT context FROM telegram_sessions WHERE session_id = %s
                """, (self.session_id,))
                row = cur.fetchone()
                context = row['context'] if row and row['context'] else {
                    'messages': [], 'summary': '', 'topics': [], 'last_specialist': None
                }

                # Add new message
                message = {
                    'role': role,
                    'content': content[:1000],  # Truncate long messages
                    'timestamp': datetime.now().isoformat(),
                    'specialist': specialist,
                    'audit_hash': audit_hash
                }
                context['messages'].append(message)

                # Keep only recent messages
                if len(context['messages']) > MAX_HISTORY_MESSAGES:
                    # Compress old messages into summary
                    old_msgs = context['messages'][:-MAX_HISTORY_MESSAGES]
                    summary_parts = [f"[{m['role']}] {m['content'][:100]}..." for m in old_msgs]
                    context['summary'] += '\n' + '\n'.join(summary_parts[-5:])
                    context['summary'] = context['summary'][-MAX_CONTEXT_LENGTH:]
                    context['messages'] = context['messages'][-MAX_HISTORY_MESSAGES:]

                # Update last specialist
                if specialist:
                    context['last_specialist'] = specialist

                # Extract topics from user messages
                if role == 'user':
                    topics = self._extract_topics(content)
                    for topic in topics:
                        if topic not in context.get('topics', []):
                            context.setdefault('topics', []).append(topic)
                    context['topics'] = context['topics'][-10:]  # Keep last 10 topics

                # Save updated context
                cur.execute("""
                    UPDATE telegram_sessions
                    SET context = %s, last_active = NOW(),
                        expires_at = NOW() + INTERVAL '%s hours'
                    WHERE session_id = %s
                """, (json.dumps(context), SESSION_EXPIRY_HOURS, self.session_id))

                conn.commit()
        finally:
            conn.close()

    def _extract_topics(self, text: str) -> List[str]:
        """Extract topic keywords from text."""
        keywords = [
            'security', 'performance', 'database', 'deploy', 'monitor',
            'gateway', 'council', 'thermal', 'memory', 'telegram',
            'redfin', 'bluefin', 'greenfin', 'sasass', 'vllm',
            'halo', 'jr', 'agent', 'task', 'pheromone', 'stigmergy'
        ]
        text_lower = text.lower()
        return [k for k in keywords if k in text_lower]

    def build_context_prompt(self) -> str:
        """
        Build a context string for injecting into Council prompts.
        Returns a summary of the conversation so far.
        """
        context = self.get_context()
        parts = []

        # Add summary if exists
        if context.get('summary'):
            parts.append(f"[Previous conversation summary: {context['summary'][-500:]}]")

        # Add recent messages
        recent = context.get('messages', [])[-5:]
        if recent:
            msg_text = '\n'.join([
                f"[{m['timestamp'][:16]}] {m['role']}: {m['content'][:200]}"
                for m in recent
            ])
            parts.append(f"[Recent conversation:\n{msg_text}]")

        # Add topics
        topics = context.get('topics', [])
        if topics:
            parts.append(f"[Topics discussed: {', '.join(topics[-5:])}]")

        return '\n'.join(parts) if parts else ''

    def get_last_specialist(self) -> Optional[str]:
        """Get the last specialist that responded."""
        context = self.get_context()
        return context.get('last_specialist')

    def clear_session(self) -> None:
        """Clear the current session (start fresh)."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE telegram_sessions
                    SET context = %s, last_active = NOW()
                    WHERE session_id = %s
                """, (json.dumps({
                    'messages': [],
                    'summary': '',
                    'topics': [],
                    'last_specialist': None
                }), self.session_id))
                conn.commit()
        finally:
            conn.close()

    def get_thermal_context(self, limit: int = 3) -> str:
        """
        Get relevant thermal memories based on conversation topics.
        """
        context = self.get_context()
        topics = context.get('topics', [])

        if not topics:
            return ''

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                # Build search pattern from topics
                pattern = '%' + '%'.join(topics[-3:]) + '%'
                cur.execute("""
                    SELECT memory_hash, LEFT(original_content, 300) as content, temperature_score
                    FROM thermal_memory_archive
                    WHERE original_content ILIKE %s
                    ORDER BY temperature_score DESC, created_at DESC
                    LIMIT %s
                """, (pattern, limit))

                rows = cur.fetchall()
                if rows:
                    memories = '\n'.join([
                        f"[{row[2]:.0f}°C] {row[1]}..." for row in rows
                    ])
                    return f"[Relevant thermal memories:\n{memories}]"
                return ''
        finally:
            conn.close()


# Convenience functions
def get_or_create_session(user_id: int, chat_id: int,
                          username: str = None) -> TelegramSessionManager:
    """Get or create a session for a Telegram user."""
    return TelegramSessionManager(user_id, chat_id, username)


def get_session_stats() -> Dict[str, Any]:
    """Get statistics about active sessions."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) as total_sessions,
                    COUNT(*) FILTER (WHERE expires_at > NOW()) as active_sessions,
                    COUNT(DISTINCT user_id) as unique_users
                FROM telegram_sessions
            """)
            row = cur.fetchone()
            return {
                'total_sessions': row[0],
                'active_sessions': row[1],
                'unique_users': row[2]
            }
    finally:
        conn.close()


if __name__ == '__main__':
    # Test
    print("Testing TelegramSessionManager...")
    session = get_or_create_session(123456, 789012, 'test_user')
    print(f"Session ID: {session.session_id}")

    session.add_message('user', 'What is the status of redfin?')
    session.add_message('assistant', 'Redfin is healthy with vLLM running.', specialist='Eagle Eye')

    context = session.build_context_prompt()
    print(f"Context:\n{context}")

    stats = get_session_stats()
    print(f"Stats: {stats}")
