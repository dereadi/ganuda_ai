# Upwork Proposal: Full-Stack Engineer — LLM-Powered Document App (Production Readiness)

**Job**: Production Ready LLM Application ($45-70/hr, 3-6 months, 30+ hrs/week)
**Date**: April 2, 2026

---

## Cover Letter

I ship LLM applications to production. Not prototypes — production systems handling real traffic with real failure modes.

My current system runs three vLLM instances on a single GPU (Qwen2.5-72B + two 7B models), serves 96,000+ memories through a RAG pipeline with correction validation, and has completed 1,041 autonomous tasks without human intervention. It's been running for 7 months on sovereign hardware. You can see it live right now: ganuda.us/api/health

Your specific requirements map to what I do daily:

Code review and cleanup: I audit and refactor LLM pipelines continuously — last week I right-sized GPU memory allocation across three model instances to eliminate thermal throttling. I improve what exists rather than rewrite.

Add Claude as LLM option: My consultation ring already runs Anthropic alongside local models. I understand the API nuances — token limits, context window management, prompt caching, cost optimization. Adding Claude to your existing OpenAI/Gemini setup is straightforward.

Document processing pipeline: Sending full documents to multimodal LLMs, request queuing with concurrency control, exponential backoff — these are production patterns I've implemented. My Jr task executor uses checkpoint/rollback with a dead-letter queue for failed operations.

GCP configuration: I run production services on both local infrastructure (systemd, Caddy, PostgreSQL, WireGuard) and have deployed to cloud environments. I'll audit your RAM, autoscaling, cold starts, and cost efficiency.

I inherit codebases, improve them, and ship them. I don't propose starting over.

Darrell Reading
ganuda.us
