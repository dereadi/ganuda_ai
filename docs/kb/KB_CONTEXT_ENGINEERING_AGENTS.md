# KB Article: Context Engineering for Coding Agents

**KB ID**: KB-CONTEXT-001
**Created**: 2025-12-03
**Category**: AI Strategy / Agent Architecture
**Source**: Dex - "Advanced Context Engineering for Coding Agents" (AI Engineer Conference)
**Tags**: context engineering, coding agents, RPI, slop prevention, LLM optimization

---

## Summary

Context engineering is the practice of optimizing what goes into an LLM's context window to get better outputs. This is critical for the Cherokee AI Federation's IT Jr agents that use LLMs for code generation.

---

## The Core Problem

From survey of 100,000 developers:
- Most AI-assisted code shipping results in **rework and churn**
- AI works great for **greenfield** (new projects, simple dashboards)
- AI struggles with **brownfield** (10-year-old codebases, complex systems)
- Result: "Too much slop, tech debt factory"

---

## The Dumb Zone Concept

LLMs have a context window (~168K tokens for Claude). Performance degrades as you fill it:

```
|---------------------------|
|     SMART ZONE (0-40%)    |  <- Best results here
|---------------------------|
|     DUMB ZONE (40-100%)   |  <- Diminishing returns
|---------------------------|
```

**Key insight**: If you fill your context with MCP JSON, file searches, and noise, you're doing all your work in the dumb zone.

---

## Why Context Matters

LLMs are stateless. The ONLY way to get better output is to put better tokens in.

Every turn of the loop (picking next tool, next action), there are:
- Hundreds of right next steps
- Hundreds of wrong next steps
- The only influence is what's in the conversation so far

**Optimize for**:
1. Correctness - No incorrect information
2. Completeness - No missing information
3. Size - Minimize noise
4. Trajectory - Avoid error patterns

---

## The Trajectory Problem

If your conversation looks like:
1. Agent does something wrong
2. Human yells at it
3. Agent does something wrong
4. Human yells at it

The LLM predicts: "Next token should be me doing something wrong so human can yell at me again."

**Solution**: Start fresh context windows when off-track. Don't try to correct repeatedly.

---

## Research-Plan-Implement (RPI) Workflow

### Phase 1: Research
- Understand how the system works
- Find the right files
- Stay objective
- **Compress truth** into a research document

Output: "Exact files and line numbers that matter"

### Phase 2: Plan
- Outline exact steps
- Include file names and line snippets
- Be explicit about testing after each change
- Include actual code snippets of what will change

**Goal**: A plan so clear that "the dumbest model in the world probably won't screw it up"

### Phase 3: Implement
- Execute the plan step by step
- Keep context low
- Test after each change

---

## Compaction Strategy

**Intentional Compaction**: Before starting new work, compress existing context into a markdown file:
- What we're working on
- Exact files and line numbers
- Decisions made
- What was tried and failed

The new agent gets straight to work instead of searching/understanding.

**When to compact**:
- At 40% context usage
- When switching tasks
- When you see "I apologize for the confusion" (time to start over)

---

## Sub-Agents Done Right

**WRONG**: Front-end agent, backend agent, QA agent (anthropomorphizing roles)

**RIGHT**: Sub-agents for controlling context
- Fork a new context window
- Go find how something works (lots of file reading)
- Return a succinct message: "The file you want is here"
- Parent agent reads that one file, gets to work

---

## On-Demand vs Pre-Built Context

**Pre-built documentation** (claude.md, README files):
- Gets out of date quickly
- The more documentation, the more lies
- Uses smart zone just to learn how system works

**On-demand compressed context** (preferred):
- Give agent steering about what part of codebase
- Launch sub-agents to take vertical slices
- Build research document that is a snapshot of actual truth
- Compress truth, not opinions

---

## Mental Alignment

The most important part of code review is keeping everyone on the same page about how the codebase is changing and why.

With AI shipping 2-3x more code:
- Reading plans is enough for technical leadership
- Plans catch problems early
- Put prompt threads on PRs so reviewers see the journey

---

## Don't Outsource the Thinking

> "AI cannot replace thinking. It can only amplify the thinking you have done or the lack of thinking you have done."

- A bad line of code = 1 bad line
- A bad part of a plan = 100 bad lines
- A bad line of research = entire thing is hosed

**Human effort should focus on highest leverage parts**:
1. Reviewing research (highest leverage)
2. Reviewing plans
3. Reviewing code (lowest leverage per line)

---

## When to Use RPI

| Task Complexity | Approach |
|-----------------|----------|
| Change button color | Just talk to agent |
| Small feature | Simple plan |
| Medium feature, multiple repos | Research + Plan |
| Complex brownfield changes | Full RPI with compaction |

"It takes reps. You will get it wrong. Pick one tool and get some reps."

---

## Cherokee AI Federation Application

### For IT Jr Agents:

1. **Research Phase**: Jr Agent should first understand relevant codebase sections
2. **Plan Phase**: Create explicit step-by-step plan with file paths and code snippets
3. **Implement Phase**: Execute plan, test after each change

### For Thermal Memory:
- Acts as compacted context across sessions
- Chiefs decisions compress intent
- Jr work reports compress what was done

### For LLM Code Generation:
- Keep prompts focused and specific
- Include exact file paths and line numbers
- Don't dump entire codebase into context
- Use sub-agents (explore agents) to find relevant files first

### Prevent Slop:
- Research before coding
- Plan before implementing
- Test after each change
- Human review at plan stage, not just code stage

---

## Key Quotes

> "The more you use the context window, the worse outcomes you'll get."

> "There is no perfect prompt. There is no silver bullet."

> "99% of your code will be shipped by AI - the hard part is adapting your team and workflow."

> "If cultural change doesn't come from the top, it won't work."

---

## Related Documents

- `/Users/Shared/ganuda/kb/KB_LLM_INTEGRATION_JR_AGENT.md` - Jr Agent LLM setup
- `/Users/Shared/ganuda/kb/KB_AI_METRICS_EVALUATION.md` - AI metrics
- `/Users/Shared/ganuda/IT_JR_LLM_SDLC_WORKFLOW.md` - SDLC workflow

---

**Temperature**: 0.80 (Knowledge Base - Strategic Reference)
