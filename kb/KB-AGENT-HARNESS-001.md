# KB-AGENT-HARNESS-001: Anthropic Long-Running Agent Harness Patterns

**Created**: 2025-12-11
**Author**: Claude TPM
**Status**: Active
**Source**: Anthropic open-source harness (December 2025)

---

## Overview

Anthropic released an open-source harness for building long-running autonomous coding agents. This KB captures the key patterns that could enhance Cherokee Jr.

---

## Core Concept

The harness enables coding agents to work for **hours or days** without overwhelming context windows by:
1. Splitting work between different agents/sessions
2. Using file-based state to communicate between sessions
3. Test-driven development to define "done"

---

## Three Core Artifacts

### 1. feature_list.json
A JSON file containing ALL test cases that must pass for the project to be complete.

```json
{
  "features": [
    {
      "id": "feat-001",
      "category": "authentication",
      "description": "User can log in with email/password",
      "validation_steps": [
        "Navigate to /login",
        "Enter valid credentials",
        "Click submit",
        "Verify redirect to dashboard"
      ],
      "passes": false
    }
  ]
}
```

Key points:
- 200+ test cases generated from PRD
- Each has `passes: true/false`
- Agent marks `passes: true` after validation
- Agent CANNOT modify validation_steps (prevents cheating)

### 2. init.sh
Initialization script that spins up the project:
- Start development servers
- Initialize databases
- Set up environment
- Called at the start of each session

### 3. claude_progress.md
Summary file updated at the END of each session:
- What was accomplished
- What features were implemented
- Any issues encountered
- Overview of previous sessions

This is the **memory bridge** between sessions.

---

## Two-Phase Architecture

### Phase 1: Initializer Agent (Session 1)
- Reads app spec / PRD
- Creates `feature_list.json` with all test cases
- Creates `init.sh` for project setup
- Creates project scaffolding/boilerplate
- Initializes git repo
- Writes initial `claude_progress.md`
- **Does NOT implement features**

### Phase 2: Coding Agents (Sessions 2+)
Loop for each session:
1. **Prime**: Read `claude_progress.md`, `feature_list.json`, git history
2. **Init**: Run `init.sh` to spin up servers
3. **Regression Test**: Spot-check recently passed features still work
4. **Pick Feature**: Choose next `passes: false` feature
5. **Implement**: Write the code
6. **Validate**: Use Puppeteer MCP to visually verify
7. **Update**: Mark `passes: true` in JSON
8. **Save State**: Git commit
9. **Handoff**: Update `claude_progress.md`
10. **End Session** → New context window starts fresh

---

## Key Patterns to Apply to Cherokee Jr

### 1. Feature List as Progress Tracker
Instead of just kanban tasks, Jr could maintain a `feature_list.json` per mission with granular test cases.

### 2. Session Handoff File
Our Jr already uses mission files, but adding a `jr_progress.md` that's updated after each work session would improve continuity.

### 3. Regression Testing
Before starting new work, Jr should verify previous work still functions.

### 4. Git Commits as Checkpoints
Each completed feature → git commit. Enables rollback if next session breaks things.

### 5. Visual Validation
The Puppeteer MCP server for browser automation could be useful for testing Telegram bot interactions or web interfaces.

---

## Implementation Ideas for Cherokee

### Enhanced Jr Mission Format
```json
{
  "mission_id": "SAG-EXAMPLE-001",
  "progress_file": "/ganuda/jr_progress/SAG-EXAMPLE-001.md",
  "feature_list": [
    {
      "id": "1",
      "description": "Add /futureself command",
      "validation": ["Run /futureself with no args shows usage", "Run /futureself 25 engineer generates 3 scenarios"],
      "passes": false
    }
  ],
  "current_session": 1,
  "total_sessions": 0
}
```

### Session Handoff Template
```markdown
# Jr Progress: SAG-EXAMPLE-001

## Session 3 Summary (2025-12-11)
- Implemented feature 1: /futureself command
- Verified in Telegram: shows usage correctly
- Created feature 2 scaffolding

## Previous Sessions
- Session 2: Set up database tables
- Session 1: Created initial file structure

## Next Steps
- Implement LLM prompt builder
- Add response chunking for Telegram
```

---

## Claude Agent SDK Notes

The harness uses the Claude Agent SDK (not CLI) for programmatic control:
- Restrict file operations to project directory
- Define allowed bash commands
- Attach MCP servers (Puppeteer)
- Auto-accept all edits (no human approval)
- Security hooks for command validation

```python
client = claude_sdk.Client(
    project_directory="/path/to/project",
    sandbox_enabled=True,
    permissions={"accept_all_edits": True},
    allowed_commands=[...],
    mcp_servers=["puppeteer"]
)
```

---

## Metrics from Demo

- **24 hours** of autonomous coding
- **54 coding agent sessions**
- **54% tests passing** (100+ of 200)
- Built a functional Claude.ai clone
- Used Claude Opus 4.5

---

## References

- Anthropic article: [link in video description]
- Open source repo: [link in video description]
- Related: KB-JR-EXECUTOR-001.md

---

**For Seven Generations**: Build systems that can work while we rest, extending our reach across time.
