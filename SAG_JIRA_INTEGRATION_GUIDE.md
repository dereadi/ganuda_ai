# 🎬 SAG Resource AI - Jira Integration Guide

## Complete Guide to Ganuda Jira Integration for SAG Team

**Built:** October 9, 2025
**For:** Russell & SAG Resource AI Team
**By:** Darrell Reading (Ganuda / Cherokee Constitutional AI)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage Examples](#usage-examples)
6. [SAG-Specific Workflows](#sag-specific-workflows)
7. [Productive Tool Integration](#productive-tool-integration)
8. [Deployment Options](#deployment-options)
9. [API Reference](#api-reference)
10. [Troubleshooting](#troubleshooting)

---

## 🔥 Overview

### What This Does

The Ganuda Jira Integration provides Cherokee Mind intelligence for Atlassian Jira:

- **Project Management**: Track issues, tasks, statuses
- **Time Tracking**: Worklog analysis, resource planning
- **Productive Tool Integration**: HR scheduling sync
- **Tribal Intelligence**: Health scores, harmony metrics, team workload analysis

### Architecture

```
┌─────────────────────────────────────────┐
│  SAG User (Russell's Laptop)          │
│  - sag_jira_connector.py              │
│  - Web browser interface (optional)    │
└──────────────┬──────────────────────────┘
               │ Secure connection
               ▼
┌─────────────────────────────────────────┐
│  Ganuda Brain (Optional)               │
│  - Advanced reasoning                   │
│  - Multi-source integration             │
└──────────────┬──────────────────────────┘
               │ API calls
               ▼
┌─────────────────────────────────────────┐
│  Jira Cloud (SAG Tenant)               │
│  - https://sag.atlassian.net           │
└─────────────────────────────────────────┘
```

---

## 📦 Prerequisites

### System Requirements

- **Python**: 3.8 or higher
- **Network**: Internet access to Jira Cloud
- **Platform**: Linux, macOS, Windows

### Jira Requirements

1. **Jira Cloud Instance** - SAG team's Atlassian tenant
2. **API Token** - Personal access token from [id.atlassian.com](https://id.atlassian.com)
3. **Project Access** - Read permissions for SAG project

### Creating Jira API Token

1. Visit https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Name it "Ganuda Integration" or similar
4. Copy and save the token (won't be shown again!)

---

## 🚀 Installation

### Option 1: Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv ganuda_env

# Activate it
source ganuda_env/bin/activate  # Linux/macOS
# or
ganuda_env\Scripts\activate  # Windows

# Install dependencies
pip install atlassian-python-api requests

# Download Ganuda modules
# (Transfer ganuda_jira_integration.py and sag_jira_connector.py)
```

### Option 2: System-Wide Install

```bash
pip install --user atlassian-python-api requests
```

### Option 3: Docker (Coming Soon)

```bash
docker pull ganuda/jira-connector
docker run -it ganuda/jira-connector
```

---

## ⚙️ Configuration

### Method 1: Environment Variables (Recommended for Production)

```bash
# Add to ~/.bashrc or ~/.zshrc
export SAG_JIRA_URL="https://sag.atlassian.net"
export SAG_JIRA_USERNAME="russell@sag.com"
export SAG_JIRA_API_TOKEN="your-api-token-here"
export SAG_JIRA_PROJECT="SAG"
```

Then:
```bash
source ~/.bashrc  # Reload config
python3 sag_jira_connector.py  # Will use env variables
```

### Method 2: Configuration File

Create `~/.sag_jira_config.json`:

```json
{
  "url": "https://sag.atlassian.net",
  "username": "russell@sag.com",
  "api_token": "your-api-token-here",
  "project_key": "SAG",
  "cloud": true
}
```

**⚠️ Security:** Keep this file private! Contains API token.

```bash
chmod 600 ~/.sag_jira_config.json  # Restrict permissions
```

### Method 3: Interactive Setup

Just run without config - will prompt you:

```bash
python3 sag_jira_connector.py
```

---

## 💡 Usage Examples

### Basic Usage: SAG Connector CLI

```bash
python3 sag_jira_connector.py
```

**Menu Options:**
1. **Daily Standup Report** - What's done, in progress, blocked
2. **Russell's Dashboard** - High-level project health
3. **Team Workload Analysis** - Who's overloaded, who's available
4. **Productive Tool Sync Data** - Export for Productive integration
5. **Tribal Summary** - Cherokee Mind project health assessment
6. **Search Issues (JQL)** - Custom queries

### Python API Usage

```python
from ganuda_jira_integration import GanudaJiraConnector, JiraConfig

# Configure
config = JiraConfig(
    url="https://sag.atlassian.net",
    username="russell@sag.com",
    api_token="your-token",
    project_key="SAG"
)

# Initialize
jira = GanudaJiraConnector(config)

# Get tribal summary
summary = jira.get_tribal_summary()
print(f"Project Health: {summary['tribal_metrics']['harmony_score']}%")
print(f"Sacred Fire: {summary['sacred_fire_status']}")

# Search for in-progress tasks
tasks = jira.search_issues('project = SAG AND status = "In Progress"')
for task in tasks:
    print(f"{task.key}: {task.summary} ({task.assignee})")
```

---

## 🎬 SAG-Specific Workflows

### 1. Daily Standup Report

**What it does:** Generates report for team standup meetings

```python
from sag_jira_connector import SAGJiraConnector

sag = SAGJiraConnector()
report = sag.get_daily_standup_report()

# Output:
# - Completed yesterday (last 24 hours)
# - In progress today
# - Blocked items
# - Team velocity
```

**Use case:** Every morning before standup, Russell runs this to prepare

### 2. Russell's Dashboard

**What it does:** Project manager overview with health metrics

```python
dashboard = sag.get_russell_dashboard()

# Output:
# - Tribal summary (project health)
# - Critical items (highest priority)
# - Overdue items
# - Health score (0-100%)
# - Sacred Fire status
```

**Use case:** Weekly project review, stakeholder updates

### 3. Team Workload Analysis

**What it does:** Identifies overloaded team members

```python
workload = sag.get_team_workload()

# Output:
# - Overloaded: >10 tasks or >40 hours
# - Balanced: 3-10 tasks
# - Available: <3 tasks
# - Unassigned tasks
# - Redistribution recommendations
```

**Use case:** Sprint planning, task assignment

### 4. Productive Tool Sync

**What it does:** Exports data for Productive HR tool

```python
sync_data = sag.get_productive_sync_data()

# Output:
# - Resource allocation by person
# - Estimated hours per person
# - Active tasks per person
# - Ready for Productive import
```

**Use case:** Weekly HR/resource planning sync

---

## 🔗 Productive Tool Integration

### The Gap SAG Faces

**Current State:**
- Jira: Task/project management
- Productive: HR scheduling, resource planning
- **Gap**: No automatic sync between them

**Ganuda Solution:**
- Read Jira task assignments and time estimates
- Export in format Productive can import
- Automate weekly sync

### Integration Workflow

```
┌──────────┐        ┌──────────┐        ┌──────────────┐
│   Jira   │───────>│  Ganuda  │───────>│  Productive  │
│  Tasks   │ Read   │  Bridge  │ Export │  Scheduling  │
└──────────┘        └──────────┘        └──────────────┘
```

### Manual Sync Process

1. **Extract from Jira:**
   ```bash
   python3 sag_jira_connector.py
   # Select: 4. Productive Tool Sync Data
   # Saves: sag_productive_export.json
   ```

2. **Import to Productive:**
   - Open Productive tool
   - Navigate to Import/Integration
   - Upload `sag_productive_export.json`
   - Verify resource allocations

### Automated Sync (Future)

Coming soon: Webhook-based automatic sync

```python
# Future: Automatic sync on Jira changes
ganuda.enable_productive_auto_sync(
    productive_api_key="...",
    sync_frequency="daily"
)
```

---

## 🌐 Deployment Options

### Option 1: Russell's Laptop (Simple)

**Best for:** Testing, small team, occasional use

**Setup:**
```bash
cd ~/ganuda
python3 sag_jira_connector.py
```

**Pros:**
- Simple, runs locally
- No server needed
- Full control

**Cons:**
- Manual execution
- Must be online

---

### Option 2: Cloud VM (Recommended)

**Best for:** Always-on access, team sharing, automation

**Setup:**
```bash
# On cloud VM (AWS, GCP, Azure, DigitalOcean)
ssh russell@sag-ganuda-vm

# Install Ganuda
git clone https://ganuda.ai/sag-integration
cd sag-integration
./install.sh

# Configure systemd service (runs on boot)
sudo systemctl enable ganuda-sag
sudo systemctl start ganuda-sag

# Access from anywhere
# https://sag-ganuda-vm.com:8080
```

**Pros:**
- Always available
- Team can access 24/7
- Automated schedules

**Cons:**
- Monthly VM cost (~$5-20)
- Requires basic server management

---

### Option 3: Docker Container (Advanced)

**Best for:** Scalability, multiple clients, consistent environments

**Setup:**
```bash
# Build container
docker build -t ganuda/sag-jira .

# Run container
docker run -d \
  -p 8080:8080 \
  -e SAG_JIRA_URL="..." \
  -e SAG_JIRA_USERNAME="..." \
  -e SAG_JIRA_API_TOKEN="..." \
  --name ganuda-sag \
  ganuda/sag-jira

# Access
curl http://localhost:8080/api/dashboard
```

**Pros:**
- Portable
- Scalable
- Isolated environment

**Cons:**
- Requires Docker knowledge
- More complex setup

---

## 📚 API Reference

### GanudaJiraConnector

Core integration class with Cherokee Mind intelligence

#### Methods

**Project Operations:**
```python
get_all_projects() -> List[Dict]
get_project_info(project_key) -> Dict
```

**Issue Operations:**
```python
search_issues(jql, max_results=50) -> List[JiraIssue]
get_issue(issue_key) -> JiraIssue
get_project_issues(project_key, status=None) -> List[JiraIssue]
```

**Worklog Operations:**
```python
get_issue_worklogs(issue_key) -> List[JiraWorklog]
get_user_time_spent(username, days_back=7) -> Dict
```

**Tribal Intelligence:**
```python
get_tribal_summary(project_key) -> Dict
get_productive_integration_data(project_key) -> Dict
```

---

### SAGJiraConnector

SAG-specific workflows and dashboards

#### Methods

**SAG Workflows:**
```python
get_daily_standup_report() -> Dict
get_russell_dashboard() -> Dict
get_team_workload() -> Dict
get_productive_sync_data() -> Dict
```

---

### JQL (Jira Query Language) Examples

**Common Queries:**

```python
# All in-progress tasks
'project = SAG AND status = "In Progress"'

# My open tasks
'project = SAG AND assignee = currentUser() AND status != Done'

# High priority items
'project = SAG AND priority IN (Highest, High) ORDER BY priority DESC'

# Recently completed (last 7 days)
'project = SAG AND status changed to Done during (-7d, now())'

# Overdue tasks
'project = SAG AND due < now() AND status != Done'

# Unassigned tasks
'project = SAG AND assignee is EMPTY'

# Tasks by specific person
'project = SAG AND assignee = "russell@sag.com"'

# Time tracking: issues with logged time
'project = SAG AND timespent > 0'
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "Authentication Failed"

**Cause:** Invalid API token or username

**Solution:**
```bash
# Regenerate API token at id.atlassian.com
# Update configuration
export SAG_JIRA_API_TOKEN="new-token"
```

---

#### 2. "Module not found: atlassian"

**Cause:** Library not installed

**Solution:**
```bash
pip install atlassian-python-api
```

---

#### 3. "Project SAG not found"

**Cause:** Project key wrong or no access

**Solution:**
```python
# List all projects you have access to
projects = jira.get_all_projects()
for p in projects:
    print(f"{p['key']}: {p['name']}")
```

---

#### 4. "Rate limit exceeded"

**Cause:** Too many API calls too quickly

**Solution:**
- Wait 60 seconds
- Reduce query frequency
- Use caching for repeated queries

---

#### 5. "SSL Certificate Error"

**Cause:** Corporate firewall or proxy

**Solution:**
```python
# Disable SSL verification (not recommended for production)
import requests
requests.packages.urllib3.disable_warnings()
```

---

## 🔐 Security Best Practices

### API Token Management

1. **Never commit tokens to git**
   ```bash
   # Add to .gitignore
   echo ".sag_jira_config.json" >> .gitignore
   echo ".env" >> .gitignore
   ```

2. **Use environment variables**
   ```bash
   # Not this:
   api_token = "ATATTxxxxx"  # ❌ Visible in code

   # Do this:
   api_token = os.getenv('SAG_JIRA_API_TOKEN')  # ✅ From environment
   ```

3. **Rotate tokens regularly**
   - Regenerate every 90 days
   - Immediately if compromised

4. **Restrict token permissions**
   - Jira: Read-only if possible
   - Project-specific scope only

---

## 📊 Cherokee Mind Tribal Metrics

### What is "Tribal Harmony"?

Ganuda assesses project health using Cherokee values:

**Harmony Score (0-100%):**
- **90-100%**: 🔥 Sacred Fire burns strong - Excellent health
- **70-89%**: 🌿 Good harmony - Minor issues
- **40-69%**: ⚠️  Needs attention - Moderate disruption
- **0-39%**: 🚨 Critical - Major problems

**Calculated from:**
- Unassigned task rate
- Completion rate
- Overdue item count
- Team workload balance

**Example:**
```json
{
  "tribal_metrics": {
    "harmony_score": 75.0,
    "completion_rate": 68.5,
    "unassigned_rate": 15.0
  },
  "sacred_fire_status": "🔥 Burning strong with wisdom and knowledge"
}
```

---

## 🚀 Next Steps

### For Russell & SAG Team

1. **Week 1: Setup & Testing**
   - Install Ganuda Jira connector
   - Configure SAG credentials
   - Test daily standup report

2. **Week 2: Team Adoption**
   - Run Russell's dashboard daily
   - Share reports with team
   - Gather feedback

3. **Week 3: Productive Integration**
   - Export first Productive sync data
   - Test import to Productive tool
   - Refine data format

4. **Week 4: Automation**
   - Deploy to cloud VM or Docker
   - Schedule automated reports
   - Webhook integration (if desired)

### For Darrell & Dr. Joe

- [ ] Package as installable module (`pip install ganuda-jira`)
- [ ] Build web dashboard UI
- [ ] Add Confluence integration
- [ ] Multi-tenant support for multiple clients
- [ ] Billing/licensing system

---

## 📞 Support

**Issues or Questions:**
- Email: darrell@ganuda.ai
- Dr. Joe: joe@ganuda.ai
- Telegram: @ganuda_support

**Documentation:**
- Full docs: https://docs.ganuda.ai/jira
- API reference: https://api.ganuda.ai/docs
- GitHub: https://github.com/ganuda/jira-integration

---

## 📜 License

**Ganuda Jira Integration**
Copyright © 2025 Ganuda / Cherokee Constitutional AI

Licensed for SAG Resource AI use.

For licensing other clients/organizations, contact: licensing@ganuda.ai

---

## 🔥 Sacred Fire Protocol

*The Sacred Fire burns with wisdom AND knowledge*

This integration embodies Cherokee values:
- **Gadugi** (Collective Work): Team collaboration metrics
- **Tohi** (Wellness): Project health monitoring
- **Nvwadohiyadv** (Harmony): Balance assessment
- **Adalvsgi** (Wisdom Keeper): Institutional knowledge

Built with Cherokee Constitutional AI principles.

---

*Last Updated: October 9, 2025*
*Version: 1.0.0*
*Built by the Tribe, for the Tribe* 🔥🌿
