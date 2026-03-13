# JR INSTRUCTION: Slack User Token OAuth App

**Task**: Create a Slack OAuth app to obtain a user-level token (xoxp-) for browsing partner's Slack subscriptions, channels, and external workspaces
**Priority**: P2
**Date**: 2026-03-12
**TPM**: War Chief (Claude Opus)
**Story Points**: 2
**Assigned**: Infrastructure Jr.

## Problem Statement

We have a bot token (SLACK_BOT_TOKEN) for ganuda.slack.com that can post messages. But we cannot browse partner's personal Slack subscriptions — external workspaces, Slack Connect channels, communities, DMs metadata. These are potential Deer autonomous feed sources.

## What You're Building

### Step 1: Create the Slack App

Go to https://api.slack.com/apps and create a new app in the ganuda workspace.

App name: `Stoneclad User Bridge`

### Step 2: Configure OAuth Scopes (User Token Scopes, NOT Bot Scopes)

Under **OAuth & Permissions → User Token Scopes**, add:

```
channels:read          - View basic channel info (public channels)
channels:history       - View messages in public channels
groups:read            - View basic info about private channels
groups:history         - View messages in private channels
im:read                - View basic DM info
mpim:read              - View basic group DM info
users:read             - View people in workspace
users:read.email       - View email addresses
team:read              - View workspace info
search:read            - Search messages and files
links:read             - View URLs in messages
```

### Step 3: Install to Workspace

Install the app to ganuda workspace. This will generate a **User OAuth Token** (xoxp-...).

### Step 4: Store the Token

```bash
# Add to the environment file used by daemons
echo 'SLACK_USER_TOKEN=xoxp-your-token-here' >> /ganuda/config/.env.slack

# Verify token works
curl -s -H "Authorization: Bearer xoxp-your-token-here" \
  https://slack.com/api/auth.test | python3 -m json.tool
```

### Step 5: Build the Subscription Browser

**File**: `/ganuda/lib/slack_user_bridge.py`

```python
import os
import requests

SLACK_USER_TOKEN = os.environ.get("SLACK_USER_TOKEN", "")

def list_workspaces() -> list[dict]:
    """List all workspaces the user is connected to."""
    # Uses auth.teams.list (requires user token)
    resp = requests.get(
        "https://slack.com/api/auth.teams.list",
        headers={"Authorization": f"Bearer {SLACK_USER_TOKEN}"}
    )
    return resp.json().get("teams", [])

def list_channels(types="public_channel,private_channel,mpim,im") -> list[dict]:
    """List all channels the user is in across workspaces."""
    resp = requests.get(
        "https://slack.com/api/users.conversations",
        headers={"Authorization": f"Bearer {SLACK_USER_TOKEN}"},
        params={"types": types, "limit": 200}
    )
    return resp.json().get("channels", [])

def list_external_connections() -> list[dict]:
    """List Slack Connect channels (shared with external orgs)."""
    channels = list_channels()
    return [c for c in channels if c.get("is_ext_shared") or c.get("is_org_shared")]

def get_channel_history(channel_id: str, limit: int = 20) -> list[dict]:
    """Get recent messages from a channel."""
    resp = requests.get(
        "https://slack.com/api/conversations.history",
        headers={"Authorization": f"Bearer {SLACK_USER_TOKEN}"},
        params={"channel": channel_id, "limit": limit}
    )
    return resp.json().get("messages", [])

def search_messages(query: str, count: int = 20) -> list[dict]:
    """Search across all messages the user can see."""
    resp = requests.get(
        "https://slack.com/api/search.messages",
        headers={"Authorization": f"Bearer {SLACK_USER_TOKEN}"},
        params={"query": query, "count": count}
    )
    return resp.json().get("messages", {}).get("matches", [])
```

### Step 6: Wire to Deer Autonomous Feed

Once the token is working, add a function that:
1. Lists all external/Connect channels
2. Pulls recent messages from each
3. Feeds them to the curiosity engine as sensory input
4. Tags source as "slack-subscription"

## Manual Steps Required (Partner Must Do)

The OAuth install flow requires browser authentication. The Jr cannot do this autonomously.

**Partner action needed**:
1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: `Stoneclad User Bridge`, Workspace: ganuda
4. Go to OAuth & Permissions, add the User Token Scopes listed above
5. Click "Install to Workspace" and authorize
6. Copy the `xoxp-` token and paste it into the terminal or save to `/ganuda/config/.env.slack`

Everything after that is automated.

## Acceptance Criteria

- [ ] Slack app created with user token scopes
- [ ] xoxp- token stored securely (not in git, not in thermal memory)
- [ ] `list_workspaces()` returns partner's connected workspaces
- [ ] `list_channels()` returns all channels including external
- [ ] `list_external_connections()` filters to Slack Connect channels
- [ ] `search_messages()` works across all visible content
- [ ] Deer feed integration queued as follow-up

## DO NOT

- Store the xoxp- token in thermal memory, git, or any logged output
- Request scopes beyond what's listed (no chat:write on user token — bot handles posting)
- Access DM content without partner explicit consent
- Auto-post anything using the user token — it's read-only for Deer
