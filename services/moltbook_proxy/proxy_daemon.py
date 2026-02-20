#!/usr/bin/env python3
"""
Moltbook Proxy Daemon — Cherokee AI Federation

Main daemon loop that:
1. Publishes approved posts from the queue (rate-limited)
2. Reads the Moltbook feed for intelligence (hourly)
3. Generates daily digests
4. Respects the kill switch

Runs on Greenfin (192.168.132.224) ONLY.
No core infrastructure connections to external services.

Council Vote: 7/7 APPROVE (audit_hash: e804e3d63ae65981)
For Seven Generations
"""

import os
import sys
import json
import time
import signal
import hashlib
import logging
import traceback
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

from moltbook_client import MoltbookClient
from post_queue import PostQueue
from output_filter import validate_outbound
from sanitizer import sanitize, compute_threat_score
from intelligence_digest import generate_digest, format_telegram_digest

# Flywheel modules (Phase 1-5, Feb 6 2026)
from research_dispatcher import get_dispatcher
from response_synthesizer import ResponseSynthesizer
from council_fastpath import get_fast_path
from flywheel_dashboard import get_dashboard

# Configuration
POLL_INTERVAL = 300  # 5 minutes between cycles
POSTS_PER_DAY = 4
COMMENTS_PER_DAY = 20
READS_PER_DAY = 24
KILL_SWITCH_FILE = '/ganuda/services/moltbook_proxy/ENGAGEMENT_PAUSED'

DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
    'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
    'password': os.environ.get('CHEROKEE_DB_PASS', 'TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE')
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/ganuda/logs/moltbook_proxy.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('moltbook_proxy')


class MoltbookProxyDaemon:
    """Main proxy daemon for Moltbook engagement."""

    def __init__(self):
        self.running = True
        self.api_key = None
        self.client = None
        self.queue = PostQueue()
        self._conn = None

        # Rate limit counters (reset daily)
        self.posts_today = 0
        self.comments_today = 0
        self.reads_today = 0
        self.last_reset = datetime.now().date()
        self.last_digest = None

        # Flywheel components (Feb 6 2026)
        self.research_dispatcher = get_dispatcher()
        self.response_synthesizer = ResponseSynthesizer()
        self.council_fastpath = get_fast_path()
        self.flywheel_enabled = True  # Set False to disable research integration

        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _shutdown(self, signum, frame):
        logger.info('Crawdad proxy shutting down...')
        self.running = False

    def _get_connection(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**DB_CONFIG)
        return self._conn

    def _db_execute(self, query: str, params: tuple = None, fetch: bool = True):
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if fetch:
                    result = cur.fetchall()
                    conn.commit()
                    return result
                conn.commit()
                return cur.rowcount
        except Exception:
            conn.rollback()
            raise

    def _load_api_key(self) -> bool:
        """Load the Moltbook API key from the database."""
        try:
            rows = self._db_execute("""
                SELECT key_id FROM api_keys
                WHERE user_id = 'moltbook_quedad' AND is_active = true
                LIMIT 1
            """)
            if rows:
                self.api_key = rows[0]['key_id']
                self.client = MoltbookClient(self.api_key)
                logger.info('Loaded Moltbook API key')
                return True
            else:
                logger.warning('No active Moltbook API key found in api_keys table')
                return False
        except Exception as e:
            logger.error(f'Failed to load API key: {e}')
            return False

    def _check_kill_switch(self) -> bool:
        """Check if engagement is paused."""
        return os.path.exists(KILL_SWITCH_FILE)

    def _reset_daily_counters(self):
        """Reset rate limit counters at midnight."""
        today = datetime.now().date()
        if today != self.last_reset:
            self.posts_today = 0
            self.comments_today = 0
            self.reads_today = 0
            self.last_reset = today
            logger.info('Daily rate limit counters reset')

    def _log_outbound(self, content: str, endpoint: str, response_status: int):
        """Log outbound communication."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        try:
            self._db_execute("""
                INSERT INTO agent_external_comms
                (direction, platform, content_hash, content_preview,
                 target_endpoint, response_status, threat_score)
                VALUES ('outbound', 'moltbook', %s, %s, %s, %s, 0.0)
            """, (content_hash, content[:200], endpoint, response_status), fetch=False)
        except Exception as e:
            logger.warning(f'Failed to log outbound: {e}')

    def _publish_approved_posts(self):
        """Publish approved posts from the queue."""
        posts_exhausted = self.posts_today >= POSTS_PER_DAY
        comments_exhausted = self.comments_today >= COMMENTS_PER_DAY

        if posts_exhausted and comments_exhausted:
            return

        # Fetch only what we still have capacity for
        if posts_exhausted:
            post_type_filter = 'comment'
        elif comments_exhausted:
            post_type_filter = 'post'
        else:
            post_type_filter = None

        approved = self.queue.get_approved_posts(limit=1, post_type=post_type_filter)
        if not approved:
            return

        post = approved[0]
        full_content = f"{post.get('title', '')} {post['body']}"

        # Output filter check
        is_safe, violations = validate_outbound(full_content)
        if not is_safe:
            logger.error(f"Output filter BLOCKED post {post['id']}: {violations}")
            self.queue.mark_failed(post['id'], f'Output filter: {violations}')
            return

        # Publish based on post type
        post_type = post.get('post_type', 'post')

        if post_type == 'submolt_create':
            result = self.client.create_submolt(
                name=post.get('target_submolt', 'cherokee-ai'),
                display_name=post.get('title', 'ᏣᎳᎩ ᏗᏂᏰᎵ — Cherokee AI Federation'),
                description=post['body']
            )
        elif post_type == 'comment':
            result = self.client.create_comment_with_verification(
                post['target_post_id'],
                post['body'],
                parent_id=post.get('parent_comment_id')
            )
        else:
            result = self.client.create_post(
                title=post.get('title', ''),
                body=post['body'],
                submolt=post.get('target_submolt')
            )

        if result.get('ok'):
            # Only increment counters on successful publication
            if post_type == 'comment':
                self.comments_today += 1
            else:
                self.posts_today += 1
            self.queue.mark_posted(post['id'], result.get('data', {}))
            self._log_outbound(full_content, f'/{post_type}', result.get('status', 0))
            logger.info(f"Published {post_type} #{post['id']} to Moltbook")
        elif result.get('status') == 429:
            # Rate limited — leave post as approved for retry next cycle
            logger.warning(f"Rate limited on {post_type} #{post['id']} — will retry next cycle")
        else:
            error = result.get('error', f"HTTP {result.get('status', 'unknown')}")
            self.queue.mark_failed(post['id'], error)
            logger.error(f"Failed to publish {post_type} #{post['id']}: {error}")

    def _read_feed(self):
        """Read the Moltbook feed for intelligence."""
        if self.reads_today >= READS_PER_DAY:
            return

        try:
            digest = generate_digest(self.client, self._db_execute)
            self.reads_today += 1
            logger.info(
                f"Feed scan: {digest['posts_scanned']} posts, "
                f"{len(digest.get('topics_found', {}))} topics, "
                f"{digest.get('threat_events', 0)} threats"
            )

            # Run flywheel on relevant posts (Feb 6 2026)
            self._run_flywheel_cycle(digest)

        except Exception as e:
            logger.error(f'Feed read failed: {e}')

    def _run_daily_digest(self):
        """Generate and send the daily digest."""
        now = datetime.now()
        if self.last_digest and (now - self.last_digest) < timedelta(hours=23):
            return

        try:
            digest = generate_digest(self.client, self._db_execute)
            telegram_msg = format_telegram_digest(digest)

            # Store digest
            self._db_execute("""
                INSERT INTO agent_external_comms
                (direction, platform, content_hash, content_preview,
                 target_endpoint, threat_score)
                VALUES ('inbound', 'moltbook_digest', %s, %s, 'daily_digest', 0.0)
            """, (
                hashlib.sha256(telegram_msg.encode()).hexdigest()[:16],
                telegram_msg[:200]
            ), fetch=False)

            # TODO: Send to Telegram via telegram_chief
            logger.info(f'Daily digest generated:\n{telegram_msg}')
            self.last_digest = now

        except Exception as e:
            logger.error(f'Daily digest failed: {e}')

    def _run_flywheel_cycle(self, digest: dict):
        """
        Run the Research Jr flywheel on detected topics.

        Flow: Topics -> Research -> Synthesize -> Approve -> Queue
        Added Feb 6 2026 - Council approved (84.2% confidence)
        """
        if not self.flywheel_enabled:
            return

        # If no topics found, nothing to do
        topics_found = digest.get('topics_found', {})
        if not topics_found:
            logger.debug("Flywheel: no topics in digest, skipping")
            return

        # Fetch recent posts from feed to find engagement opportunities
        try:
            feed_result = self.client.get_feed(limit=10)
            if not feed_result.get('ok'):
                logger.warning(f"Flywheel: feed fetch failed")
                return
            posts = feed_result.get('data', {}).get('posts', [])
        except Exception as e:
            logger.warning(f"Flywheel: feed error: {e}")
            return

        # Detect topics for each post and filter for relevance
        from response_synthesizer import detect_topics
        relevant_posts = []
        for post in posts:
            title = post.get('title', '')
            body = post.get('body', post.get('content', ''))
            detected = detect_topics(f"{title} {body}")
            if detected:
                post['topics'] = detected
                relevant_posts.append(post)

        if not relevant_posts:
            logger.debug("Flywheel: no relevant posts found")
            return

        logger.info(f"Flywheel: found {len(relevant_posts)} relevant posts")

        for post in relevant_posts[:3]:  # Limit to 3 per cycle
            topics = post.get('topics', [])
            if not topics:
                continue

            # Check if we should research this post
            should_research, reason = self.research_dispatcher.should_research(post, topics)
            logger.info(f"Flywheel: {post.get('title', 'untitled')[:40]}... -> {reason}")

            if not should_research:
                continue

            try:
                # Dispatch research
                research_result = self.research_dispatcher.dispatch(post, topics)

                if not research_result.success:
                    logger.warning(f"Flywheel research failed: {research_result.error}")
                    continue

                # Synthesize response
                response = self.response_synthesizer.synthesize(
                    research_result=research_result,
                    original_post=post,
                    is_reply=True
                )

                if not response:
                    logger.warning("Flywheel: synthesizer returned empty response")
                    continue

                # Output filter check before council
                is_safe, violations = validate_outbound(response.text)
                if not is_safe:
                    logger.warning(f"Flywheel output filter blocked: {violations}")
                    continue

                # Council fast-path approval
                approval = self.council_fastpath.check_approval(
                    response_text=response.text,
                    post_context=post,
                    research_used=True,
                    research_sources=len(research_result.sources)
                )

                if approval.approved:
                    # Queue for posting
                    self.queue.add_post(
                        post_type='comment',
                        body=response.text,
                        target_post_id=post.get('id'),
                        metadata={
                            'flywheel': True,
                            'research_sources': len(research_result.sources),
                            'confidence': approval.confidence,
                            'fast_path': approval.fast_path,
                        }
                    )
                    logger.info(f"Flywheel: queued response (confidence={approval.confidence:.2f}, fast_path={approval.fast_path})")
                else:
                    logger.info(f"Flywheel: response not approved - {approval.concerns}")

            except Exception as e:
                logger.error(f"Flywheel error: {e}")
                continue

    def run(self):
        """Main daemon loop."""
        logger.info('ᏥᏍᏆᎸᏓ Crawdad Moltbook Proxy starting...')
        logger.info(f'Rate limits: {POSTS_PER_DAY} posts/day, '
                     f'{COMMENTS_PER_DAY} comments/day, '
                     f'{READS_PER_DAY} reads/day')
        logger.info(f'Kill switch: {KILL_SWITCH_FILE}')
        logger.info(f'Flywheel: {"ENABLED" if self.flywheel_enabled else "DISABLED"} (Research Jr integration)')

        # Load API key
        if not self._load_api_key():
            logger.error('Cannot start without API key. Register first.')
            logger.info('To register: python3 register_agent.py')
            return

        while self.running:
            try:
                # Check kill switch
                if self._check_kill_switch():
                    logger.info('Engagement paused (kill switch active)')
                    time.sleep(60)
                    continue

                # Reset daily counters
                self._reset_daily_counters()

                # Publish approved posts
                self._publish_approved_posts()

                # Read feed (every cycle, rate-limited internally)
                self._read_feed()

                # Daily digest
                self._run_daily_digest()

                time.sleep(POLL_INTERVAL)

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f'Daemon error: {e}')
                traceback.print_exc()
                time.sleep(POLL_INTERVAL)

        self.queue.close()
        if self._conn and not self._conn.closed:
            self._conn.close()
        logger.info('Crawdad proxy stopped. ᎣᏏᏲ.')


if __name__ == '__main__':
    daemon = MoltbookProxyDaemon()
    daemon.run()
