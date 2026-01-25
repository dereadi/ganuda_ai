# ULTRATHINK: Duplo Phase 2 - Unified Channels & Tribal Research

## Executive Summary

Building on Duplo MVP (Uktena Tool), Phase 2 unifies all communication channels through a single LLM that picks up different toolsets. Telegram, web chat, and research become **tools**, not separate systems. Research findings flow into thermal memory, creating a tribal knowledge flywheel.

> "One mind, many hands. Research once, benefit all."

## The Problem: Channel Silos

### Current State

```
┌──────────────────────────────────────────────────────────────┐
│                     SILOED CHANNELS                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  telegram_chief.py        vetassist/chat.py    jr_executor  │
│  ├── Own logic            ├── Own logic        ├── Own logic│
│  ├── Own memory           ├── Own context      ├── Own tasks│
│  ├── No web search        ├── No web search    ├── Has search│
│  └── Telegram only        └── Web only         └── Background│
│                                                              │
│  Problems:                                                   │
│  • Same questions answered differently per channel           │
│  • Research not shared across channels                       │
│  • Duplicate code, duplicate maintenance                     │
│  • Context lost between channels                             │
│  • User on Telegram can't benefit from web research          │
└──────────────────────────────────────────────────────────────┘
```

### User Pain Points

| User Action | Current Experience |
|-------------|-------------------|
| Ask question on Telegram | Gets answer from model's training only |
| Ask same question on web | Gets different answer, no web search |
| Research done by Jr | Stays in Jr reports, not accessible |
| Council votes on topic | Doesn't see prior research on topic |

## The Solution: Duplo Unified Channels

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    DUPLO UNIFIED CHANNELS                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│                    ┌─────────────────┐                       │
│                    │   NEMOTRON LLM  │                       │
│                    │   (Single Base) │                       │
│                    └────────┬────────┘                       │
│                             │                                │
│              ┌──────────────┼──────────────┐                 │
│              │              │              │                 │
│         ┌────▼────┐   ┌────▼────┐   ┌────▼────┐             │
│         │TELEGRAM │   │WEB CHAT │   │RESEARCH │             │
│         │ TOOLS   │   │ TOOLS   │   │ TOOLS   │             │
│         └────┬────┘   └────┬────┘   └────┬────┘             │
│              │              │              │                 │
│         ┌────▼────┐   ┌────▼────┐   ┌────▼────┐             │
│         │send_msg │   │stream   │   │web_search│            │
│         │get_chat │   │format   │   │arxiv     │            │
│         │buttons  │   │auth     │   │crawl     │            │
│         └─────────┘   └─────────┘   └─────────┘             │
│                             │                                │
│                    ┌────────▼────────┐                       │
│                    │ THERMAL MEMORY  │                       │
│                    │ (Tribal Share)  │                       │
│                    └─────────────────┘                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Tool Registry: Communication Tools

```python
# Telegram Channel Tools
telegram_tools = ToolSet(
    name="telegram_channel",
    tools=[
        Tool("send_message", "Send message to Telegram chat", telegram.send_message),
        Tool("send_buttons", "Send inline keyboard buttons", telegram.send_inline_keyboard),
        Tool("get_chat_context", "Get recent chat history", telegram.get_chat_history),
        Tool("send_document", "Send file/document", telegram.send_document),
        Tool("edit_message", "Edit previous message", telegram.edit_message),
    ]
)

# Web Chat Channel Tools
webchat_tools = ToolSet(
    name="webchat_channel",
    tools=[
        Tool("stream_response", "Stream response chunks to frontend", webchat.stream),
        Tool("get_session", "Get user session and auth context", webchat.get_session),
        Tool("render_markdown", "Format response as markdown", webchat.render_md),
        Tool("suggest_actions", "Suggest follow-up actions", webchat.suggest),
        Tool("save_conversation", "Save conversation to user history", webchat.save),
    ]
)

# Research Tools (shared across all channels)
research_tools = ToolSet(
    name="research",
    tools=[
        Tool("web_search", "Search the web for current information", research.web_search),
        Tool("arxiv_search", "Search arXiv for academic papers", research.arxiv_search),
        Tool("crawl_url", "Fetch and parse a specific URL", research.crawl_url),
        Tool("summarize_paper", "Summarize an academic paper", research.summarize),
        Tool("deposit_to_memory", "Save research to thermal memory", memory.deposit),
        Tool("query_memory", "Search thermal memory for prior research", memory.query),
    ]
)
```

### The Unified Handler

```python
class DuploChannelHandler:
    """
    Single handler for all communication channels.
    Picks up tools based on channel, always has research tools.
    """

    def __init__(self, llm, composer: DuploComposer):
        self.llm = llm
        self.composer = composer

    async def handle_message(self, channel: str, message: str, context: dict) -> str:
        """
        Handle incoming message from any channel.

        Args:
            channel: 'telegram', 'webchat', 'api'
            message: User's message
            context: Channel-specific context (chat_id, session, etc.)
        """
        # Always include research tools
        tools = ['research']

        # Add channel-specific tools
        if channel == 'telegram':
            tools.append('telegram_channel')
        elif channel == 'webchat':
            tools.append('webchat_channel')

        # Check thermal memory for prior research on topic
        prior_research = await self.query_prior_research(message)

        # Compose the specialist with appropriate tools
        specialist = self.composer.compose(
            role='assistant',
            tools=tools,
            context={
                'channel': channel,
                'prior_research': prior_research,
                **context
            }
        )

        # Generate response
        response = await specialist.respond(message)

        # If research was done, deposit to thermal memory
        if specialist.did_research:
            await self.deposit_research(
                query=message,
                findings=specialist.research_findings,
                channel=channel
            )

        return response

    async def query_prior_research(self, message: str) -> list:
        """Check if tribe has already researched this topic."""
        return await memory.semantic_search(
            query=message,
            memory_type='research',
            limit=5
        )

    async def deposit_research(self, query: str, findings: dict, channel: str):
        """Deposit research to thermal memory for tribal sharing."""
        await memory.insert(
            content=f"Research on: {query}\n\nFindings: {findings['summary']}",
            metadata={
                'type': 'research',
                'query': query,
                'sources': findings['sources'],
                'channel_origin': channel,
                'deposited_by': 'duplo_unified'
            },
            temperature='WHITE_HOT'  # Fresh research starts hot
        )
```

## The Research Flywheel

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    RESEARCH FLYWHEEL                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. USER ASKS QUESTION                                      │
│     ┌─────────────┐                                         │
│     │ "What are   │  ← Telegram OR Web Chat                 │
│     │  the nexus  │                                         │
│     │  letter     │                                         │
│     │  requirements│                                        │
│     │  for sleep  │                                         │
│     │  apnea?"    │                                         │
│     └──────┬──────┘                                         │
│            │                                                │
│  2. CHECK THERMAL MEMORY                                    │
│            ▼                                                │
│     ┌─────────────┐                                         │
│     │ Prior       │  → Found? Use it + supplement           │
│     │ Research?   │  → Not found? Do fresh research         │
│     └──────┬──────┘                                         │
│            │                                                │
│  3. DO RESEARCH (if needed)                                 │
│            ▼                                                │
│     ┌─────────────┐                                         │
│     │ web_search  │  → VA.gov, CCK Law, etc.               │
│     │ crawl_url   │  → Extract requirements                 │
│     │ summarize   │  → Create digestible answer            │
│     └──────┬──────┘                                         │
│            │                                                │
│  4. RESPOND TO USER                                         │
│            ▼                                                │
│     ┌─────────────┐                                         │
│     │ Answer with │  ← Via Telegram OR Web Chat tools      │
│     │ sources     │                                         │
│     └──────┬──────┘                                         │
│            │                                                │
│  5. DEPOSIT TO THERMAL MEMORY                               │
│            ▼                                                │
│     ┌─────────────┐                                         │
│     │ Tribal      │  → Next person asking benefits         │
│     │ Knowledge   │  → Council can reference               │
│     │ Grows       │  → Research compounds over time        │
│     └─────────────┘                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Flywheel Benefits

| Interaction | Without Flywheel | With Flywheel |
|-------------|------------------|---------------|
| First question on topic | Model guesses from training | Fresh web research, deposited |
| Second question (same topic) | Model guesses again | Uses prior research + supplements |
| Council votes on topic | No context | Rich research context available |
| Different channel, same topic | Starts from scratch | Instant access to prior work |
| Week later, same topic | Model guesses | Thermal memory retrieval (decayed but present) |

## Integration with Existing Systems

### Telegram Bot Refactor

```python
# BEFORE: telegram_chief.py (standalone)
async def handle_telegram_message(update, context):
    message = update.message.text
    # ... lots of custom logic ...
    response = await llm.generate(message)
    await update.message.reply_text(response)

# AFTER: telegram_chief.py (Duplo)
async def handle_telegram_message(update, context):
    handler = DuploChannelHandler(llm, composer)
    response = await handler.handle_message(
        channel='telegram',
        message=update.message.text,
        context={
            'chat_id': update.message.chat_id,
            'user_id': update.message.from_user.id,
            'username': update.message.from_user.username
        }
    )
    # Response sent via telegram_tools inside handler
```

### VetAssist Chat Refactor

```python
# BEFORE: vetassist/chat.py (standalone)
@router.post("/api/v1/chat/message")
async def chat_message(request: ChatRequest):
    response = await llm.generate(request.message)
    return {"response": response}

# AFTER: vetassist/chat.py (Duplo)
@router.post("/api/v1/chat/message")
async def chat_message(request: ChatRequest, user: User = Depends(get_user)):
    handler = DuploChannelHandler(llm, composer)
    response = await handler.handle_message(
        channel='webchat',
        message=request.message,
        context={
            'session_id': request.session_id,
            'user_id': user.id,
            'conversation_history': request.history
        }
    )
    return {"response": response}
```

### Council Integration

```python
# Council can now access tribal research
async def council_vote_with_research(question: str):
    # Query thermal memory for prior research
    prior_research = await memory.semantic_search(
        query=question,
        memory_type='research',
        limit=10
    )

    # Include in Council context
    enhanced_context = f"""
TRIBAL RESEARCH ARCHIVE (from thermal memory):
{format_research(prior_research)}

QUESTION:
{question}
"""

    return await council.vote(enhanced_context)
```

## Implementation Plan

### Phase 2a: Tool Registry (Days 1-3)
- Create `telegram_tools` ToolSet
- Create `webchat_tools` ToolSet
- Create `research_tools` ToolSet
- Register in global tool registry

### Phase 2b: Unified Handler (Days 4-6)
- Implement `DuploChannelHandler`
- Add thermal memory query/deposit
- Test with mock channels

### Phase 2c: Telegram Migration (Days 7-9)
- Refactor `telegram_chief.py` to use Duplo
- Maintain backward compatibility
- Test with real Telegram messages

### Phase 2d: VetAssist Chat Migration (Days 10-12)
- Refactor VetAssist chat endpoint
- Add research capability to web chat
- Test with real web sessions

### Phase 2e: Research Flywheel (Days 13-15)
- Implement research deposit logic
- Add semantic search for prior research
- Connect to Council voting

### Phase 2f: Validation (Days 16-17)
- Cross-channel testing
- Research accumulation verification
- Performance benchmarking

## Success Metrics

| Metric | Target |
|--------|--------|
| Research reuse rate | 30%+ of questions find prior research |
| Response quality improvement | User satisfaction +20% |
| Research deposit rate | 50%+ of questions generate deposits |
| Cross-channel consistency | Same question = same quality answer |
| Council context richness | 80%+ of votes have research context |

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Research quality varies | Crawdad reviews sources, flags unreliable |
| Memory bloat | Thermal decay naturally prunes old research |
| Channel-specific needs lost | Tool context preserves channel requirements |
| Latency increase | Research is optional, cached when possible |
| Tool conflicts | Clear tool boundaries, no overlap |

## Seven Generations Impact

### Generation 1 (Now - 2051)
Unified channels established. Research flywheel begins accumulating tribal knowledge. Users benefit regardless of channel choice.

### Generation 2 (2051 - 2076)
Research corpus grows to millions of entries. New questions increasingly answered from tribal memory. Council decisions enriched by decades of accumulated research.

### Generation 3 (2076 - 2101)
Tribal knowledge becomes self-reinforcing. Research builds on research. Emergent expertise in domains the Federation serves.

### Generation 4 (2101 - 2126)
Cross-domain insights emerge from research corpus. Connections found that no individual researcher would see.

### Generation 5 (2126 - 2151)
Research becomes predictive. System anticipates questions and pre-researches based on trends.

### Generation 6 (2151 - 2176)
Tribal memory is teaching resource. New AI systems learn from Cherokee Federation's accumulated research.

### Generation 7 (2176 - 2201)
175 years of research preserved. The flywheel has become a flywheel of flywheels - research generating research generating research.

## Dependency on Duplo MVP

This Phase 2 **requires** Duplo MVP (Uktena Tool) to succeed first:

1. MVP proves tool composition works
2. MVP validates minimal latency overhead
3. MVP establishes tool registry patterns
4. MVP demonstrates Council integration

If MVP fails, Phase 2 does not proceed. If MVP succeeds, Phase 2 builds directly on its foundation.

## Cost/Benefit Summary

```
COST:
- 17 days Jr time
- Refactor two existing systems (Telegram, VetAssist chat)
- New research tools implementation
- Thermal memory integration work

BENEFIT:
- Unified codebase (less maintenance)
- Research shared across all channels
- Users get better answers faster
- Council has richer context
- Knowledge compounds over time
- Foundation for future channel additions (Discord, SMS, etc.)
```

---

*Cherokee AI Federation - For the Seven Generations*
*"One mind, many hands. Research once, benefit all."*

---

## TPM Approval Notes (January 19, 2026)

### Council Vote: f59a93023273dc7e
- **Confidence**: 79.4%
- **Status**: APPROVED WITH CONDITIONS

### Security Reframe

Crawdad raised attack surface concerns. TPM clarification:

> **Unified channels CONSOLIDATES the attack surface - this is a security IMPROVEMENT, not an increase.**

```
BEFORE (Scattered):                 AFTER (Consolidated):
┌─────────┐ ┌─────────┐            ┌─────────────────────┐
│Telegram │ │Web Chat │            │   SINGLE GATEWAY    │
│ Endpoint│ │ Endpoint│     →      │  (Well-Defended)    │
└────┬────┘ └────┬────┘            └──────────┬──────────┘
     │           │                            │
   Attack     Attack                     One Attack
   Vector 1   Vector 2                   Vector (Hardened)
```

One well-defended gateway beats multiple scattered endpoints.

### New Requirement: Proactive Security Research

Duplo must include **daily LLM security research** as a core function:

```python
security_research_tools = ToolSet(
    name="security_research",
    tools=[
        Tool("search_cve", "Search for new CVEs affecting LLM systems", security.search_cve),
        Tool("search_llm_attacks", "Search for emerging LLM attack techniques", security.search_attacks),
        Tool("monitor_advisories", "Monitor security advisories", security.monitor_advisories),
        Tool("deposit_threat_intel", "Deposit findings to tribal security memory", security.deposit_intel),
    ]
)

# Daily job: Duplo picks up security_research_tools, searches, deposits to memory
# Council and specialists can then access threat intelligence
```

### Design Principles (TPM Mandated)

1. **Security by design** - Not bolted on after the fact
2. **Purpose-driven architecture** - Every tool serves the tribe
3. **Consolidation = fewer attack vectors** - Unified is stronger
4. **Proactive security research** - Duplo keeps tribe on cutting edge

### Approved Conditions

| # | Condition | Owner |
|---|-----------|-------|
| 1 | MVP (Uktena) must succeed first | Jr #148 |
| 2 | Security review with RBAC design | Crawdad |
| 3 | Load testing for thermal memory growth | Gecko |
| 4 | Monitoring/observability implementation | Eagle Eye |
| 5 | Cultural alignment verification | Turtle + Spider |

### TPM Final Note

> "Duplo is a strategic asset for the tribe. Manage it correctly."

---

*Approved by TPM Darrell - January 19, 2026*
*Council Vote Hash: f59a93023273dc7e*
