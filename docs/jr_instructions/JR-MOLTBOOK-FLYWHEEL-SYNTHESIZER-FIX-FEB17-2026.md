# Jr Instruction: Fix Moltbook Flywheel Synthesizer Call

**Kanban**: #1770 (adjacent — Moltbook re-enablement)
**Priority**: 9
**Assigned Jr**: Software Engineer Jr.
**use_rlm**: false
**Sprint**: RC-2026-02E

## Context

The Moltbook proxy daemon has been stopped since Feb 11 due to a bug in the flywheel cycle. The `_run_flywheel_cycle()` method in proxy_daemon.py calls `self.response_synthesizer.synthesize()` with wrong keyword arguments:

**Current (broken)**: `synthesize(post=post, topics=topics, research=research_result)`
**Expected signature**: `synthesize(self, research_result, original_post, use_greeting=False, is_reply=True)`

The kwargs `post`, `topics`, `research` don't match the method's parameters `research_result`, `original_post`. This causes `TypeError: synthesize() got an unexpected keyword argument 'post'` on every flywheel cycle.

## Step 1: Fix the synthesize() call in proxy_daemon.py

File: `/ganuda/services/moltbook_proxy/proxy_daemon.py`

<<<<<<< SEARCH
                # Synthesize response
                response = self.response_synthesizer.synthesize(
                    post=post,
                    topics=topics,
                    research=research_result
                )
=======
                # Synthesize response
                response = self.response_synthesizer.synthesize(
                    research_result=research_result,
                    original_post=post,
                    is_reply=True
                )
>>>>>>> REPLACE

## Notes

- The `topics` parameter is not used by synthesize() — topic context is already embedded in the research_result from the dispatcher
- `is_reply=True` because flywheel responses are always comments on existing posts
- `use_greeting=False` (default) is correct — greeting is only for direct mentions
- After this fix, restart moltbook-proxy service on redfin: `sudo systemctl restart moltbook-proxy`
