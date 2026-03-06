# Jr Instruction: Cloudflare WAF Agent Rate Limiting

**Kanban**: #1867
**Priority**: 5
**Story Points**: 3
**use_rlm**: false
**assigned_jr**: Software Engineer Jr.

---

## Overview

Create a Cloudflare WAF rule configuration file for agent rate limiting on DMZ-facing endpoints. This protects owlfin/eaglefin from AI scraper abuse and bot traffic. The JSON config documents the rules to be applied via Cloudflare dashboard or API. A README section is included since WAF rules require manual dashboard deployment.

---

## Steps

### Step 1: Create the WAF rules configuration

Create `/ganuda/config/cloudflare/agent-waf-rules.json`

```json
{
  "description": "Cherokee AI Federation - Cloudflare WAF Rules for Agent Rate Limiting",
  "last_updated": "2026-02-23",
  "kanban_ticket": "#1867",
  "notes": "Apply via Cloudflare Dashboard or API. These rules are NOT auto-deployed.",

  "ip_lists": {
    "federation_allowlist": {
      "name": "federation-internal",
      "description": "Federation LAN and Tailscale IPs - always allowed",
      "entries": [
        {"cidr": "192.168.132.0/24", "comment": "Federation LAN (redfin, greenfin, bluefin, bmasass)"},
        {"cidr": "100.0.0.0/8", "comment": "Tailscale network range"}
      ]
    }
  },

  "rules": [
    {
      "id": "waf-rule-001",
      "name": "Allow Federation IPs",
      "description": "Skip all WAF rules for federation internal traffic",
      "priority": 1,
      "action": "skip",
      "skip_rules": "all",
      "expression": "(ip.src in {192.168.132.0/24 100.0.0.0/8})"
    },
    {
      "id": "waf-rule-002",
      "name": "Rate Limit API Paths",
      "description": "60 requests per minute per IP for all /api/* endpoints",
      "priority": 2,
      "action": "block",
      "rule_type": "rate_limit",
      "rate_limit": {
        "requests_per_period": 60,
        "period_seconds": 60,
        "counting_expression": "(http.request.uri.path matches "^/api/.*")",
        "mitigation_timeout_seconds": 120
      },
      "expression": "(http.request.uri.path matches "^/api/.*") and not (ip.src in {192.168.132.0/24 100.0.0.0/8})"
    },
    {
      "id": "waf-rule-003",
      "name": "Challenge Known AI Agent User-Agents",
      "description": "Issue managed challenge for known AI scraper bots",
      "priority": 3,
      "action": "managed_challenge",
      "expression": "(http.user_agent contains "ClaudeBot" or http.user_agent contains "GPTBot" or http.user_agent contains "bingbot" or http.user_agent contains "Bytespider") and not (ip.src in {192.168.132.0/24 100.0.0.0/8})"
    },
    {
      "id": "waf-rule-004",
      "name": "Block Markdown Scraping Above Threshold",
      "description": "Block non-allowlisted IPs requesting text/markdown at high volume (100+ req/min)",
      "priority": 4,
      "action": "block",
      "rule_type": "rate_limit",
      "rate_limit": {
        "requests_per_period": 100,
        "period_seconds": 60,
        "counting_expression": "(http.request.headers["accept"] contains "text/markdown")",
        "mitigation_timeout_seconds": 300
      },
      "expression": "(http.request.headers["accept"] contains "text/markdown") and not (ip.src in {192.168.132.0/24 100.0.0.0/8})"
    }
  ],

  "readme": {
    "deployment_steps": [
      "1. Log into Cloudflare Dashboard for the zone",
      "2. Navigate to Security > WAF > Custom Rules",
      "3. Create an IP List named federation-internal under Manage Account > Configurations > Lists",
      "4. Add the CIDR entries from ip_lists.federation_allowlist.entries to that list",
      "5. Create each rule from the rules array in order of priority",
      "6. For rate_limit rules: navigate to Security > WAF > Rate Limiting Rules instead",
      "7. Test with: curl -H User-Agent:ClaudeBot https://your-domain/api/test -- should get challenged",
      "8. Verify federation IPs bypass all rules by testing from a Tailscale node"
    ],
    "api_deployment": [
      "Alternatively, use Cloudflare API v4:",
      "POST https://api.cloudflare.com/client/v4/zones/{zone_id}/rulesets",
      "Auth: Bearer token with Zone.Firewall Services permission",
      "Refer to https://developers.cloudflare.com/waf/custom-rules/create-api/"
    ],
    "rollback": "Delete the custom rules from the WAF dashboard. IP list can remain for reuse."
  }
}
```

---

## Verification

1. Confirm file exists at `/ganuda/config/cloudflare/agent-waf-rules.json`
2. Validate JSON syntax: `python3 -c "import json; json.load(open('/ganuda/config/cloudflare/agent-waf-rules.json'))"`
3. Confirm all 4 rules are present with correct priority ordering
4. Confirm federation allowlist includes both 192.168.132.0/24 and 100.0.0.0/8
5. Confirm readme section contains manual deployment steps
