# Jr Instruction: Agent Traffic Monitoring — Promtail + OpenObserve

**Task ID:** AGENT-TRAFFIC
**Kanban:** #1866
**Priority:** 3
**Assigned:** Software Engineer Jr.

---

## Overview

Create a Promtail pipeline stage that parses AI agent User-Agent strings and `Accept: text/markdown` headers from Caddy access logs. Push parsed fields to OpenObserve on greenfin. Hawk mandate: monitor agent traffic BEFORE expanding agentic access.

---

## Step 1: Create the Promtail agent detection pipeline config

Create `/ganuda/config/promtail/agent-detection-pipeline.yml`

```yaml
# Agent Traffic Detection Pipeline for Promtail
# Parses AI agent User-Agent strings from Caddy access logs
# Feeds into OpenObserve on greenfin for dashboard visualization
#
# Agent patterns detected:
# - Claude (Anthropic) — "ClaudeBot", "claude-agent"
# - GPT (OpenAI) — "GPTBot", "ChatGPT-User"
# - Google — "Google-Extended", "Googlebot"
# - Bing/Copilot — "bingbot"
# - CCBot — Common Crawl
# - Bytespider — TikTok/ByteDance
# - Custom agents — Accept: text/markdown, application/json

# Pipeline stages to add to existing Promtail config
pipeline_stages:
  # Parse Caddy JSON access log
  - json:
      expressions:
        request_method: request.method
        request_uri: request.uri
        status: status
        user_agent: request.headers.User-Agent[0]
        accept_header: request.headers.Accept[0]
        remote_addr: request.remote_ip
        response_size: size

  # Detect known AI agent User-Agents
  - match:
      selector: '{job="caddy-access"}'
      stages:
        - regex:
            source: user_agent
            expression: '(?i)(?P<agent_type>ClaudeBot|claude-agent|GPTBot|ChatGPT-User|Google-Extended|Googlebot|bingbot|CCBot|Bytespider|facebookexternalhit|Applebot|anthropic-ai|cohere-ai)'

        # Label agent traffic
        - labels:
            agent_type:

        # Detect markdown-accepting clients (likely agents)
        - regex:
            source: accept_header
            expression: '(?P<accepts_markdown>text/markdown)'
        - labels:
            accepts_markdown:

  # Add static labels for OpenObserve filtering
  - static_labels:
      log_type: agent_traffic

  # Timestamp from Caddy log
  - timestamp:
      source: ts
      format: Unix

  # Output format for OpenObserve
  - output:
      source: user_agent
```

---

## Step 2: Update main Promtail config to include agent pipeline

File: `/ganuda/home/dereadi/promtail/config/promtail.yaml`

Find the `scrape_configs` section and add the Caddy access log scrape job. Add this after the last existing scrape_config entry:

<<<<<<< SEARCH
  - job_name: system
=======
  - job_name: caddy_access_logs
    static_configs:
      - targets:
          - localhost
        labels:
          job: caddy-access
          host: owlfin
          __path__: /var/log/caddy/access.log

    pipeline_stages:
      - json:
          expressions:
            user_agent: request.headers.User-Agent[0]
            accept_header: request.headers.Accept[0]
            request_uri: request.uri
            status: status
            remote_addr: request.remote_ip

      - regex:
          source: user_agent
          expression: '(?i)(?P<agent_type>ClaudeBot|claude-agent|GPTBot|ChatGPT-User|Google-Extended|Googlebot|bingbot|CCBot|Bytespider|facebookexternalhit|Applebot|anthropic-ai|cohere-ai)'

      - labels:
          agent_type:

      - regex:
          source: accept_header
          expression: '(?P<accepts_markdown>text/markdown)'

      - labels:
          accepts_markdown:

  - job_name: system
>>>>>>> REPLACE

---

## Verification

After updating Promtail config, restart and check:
```text
sudo systemctl restart promtail
sudo journalctl -u promtail -n 20 --no-pager
```

Verify logs flowing to OpenObserve:
```text
curl -s 'http://greenfin:5080/api/default/caddy-access/_search' \
  -H 'Authorization: Basic ...' \
  -d '{"query": {"match_all": {}}, "size": 5}'
```

---

## Notes

- Detects 12+ known AI agent User-Agent patterns
- Also detects `Accept: text/markdown` header (Cloudflare AI agent marker)
- Caddy access logs are JSON format — pipeline uses json stage parser
- OpenObserve on greenfin receives via Promtail push API
- Agent traffic labeled separately for dashboard filtering
- Future: Build OpenObserve dashboard (separate task) showing agent vs human traffic
- Hawk mandate: understand who's crawling before expanding agentic endpoints
