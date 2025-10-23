# Ganuda Daemon - Coordinator Architecture
## Cherokee Constitutional AI - Integration Jr Deliverable

**Author**: Integration Jr (War Chief)
**Date**: October 23, 2025
**Purpose**: Define core architecture for Ganuda Desktop Assistant background daemon

---

## Executive Summary

The **Ganuda Daemon** is the heart of Cherokee Constitutional AI on the desktop. It runs silently in the background, coordinating 5 JR Workers (Memory, Meta, Executive, Conscience, Integration), managing connectors (email, calendar, files), and routing queries to either local inference or remote hub burst. This document defines its architecture, IPC model, and integration with Guardian (sacred protection layer).

**Key Design Principles:**
- **Sovereignty**: User owns all data, daemon runs locally (no cloud by default)
- **Gadugi**: JRs self-organize, daemon coordinates but doesn't dictate
- **Seven Generations**: Architecture must scale for 140+ years
- **Guardian Protection**: All queries filtered through sacred protection layer

---

## 1. Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│                     Ganuda Tray App (UI)                      │
│                  (Electron/Tauri, user-facing)                │
└────────────────────┬───────────────────────────────────────────┘
                     │ IPC (Unix Socket / Named Pipe)
                     ▼
┌────────────────────────────────────────────────────────────────┐
│                      Ganuda Daemon                             │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │             Coordinator (main.py)                        │ │
│  │  - Query Router (local vs hub burst decision)           │ │
│  │  - JR Worker Scheduler (task queue)                     │ │
│  │  - Connector Manager (email, calendar, files)           │ │
│  │  - IPC Server (Unix socket listener)                    │ │
│  └────────┬─────────────────┬────────────────┬──────────────┘ │
│           │                 │                │                 │
│           ▼                 ▼                ▼                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐        │
│  │  Guardian   │   │ JR Workers  │   │ Connectors  │        │
│  │  Module     │   │ (5 types)   │   │ (IMAP, Cal) │        │
│  └─────────────┘   └─────────────┘   └─────────────┘        │
│           │                 │                │                 │
│           ▼                 ▼                ▼                 │
│  ┌──────────────────────────────────────────────────────┐    │
│  │        Encrypted Cache (SQLite + AES-256-GCM)        │    │
│  └──────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Hub (Optional)       │
         │  WireGuard Mesh       │
         │  192.168.132.x        │
         └───────────────────────┘
```

### 1.1 Components

| Component | Responsibility | Location |
|-----------|---------------|----------|
| **Coordinator** | Main daemon process, orchestrates all subsystems | `/daemon/main.py` |
| **Query Router** | Decides local inference vs hub burst | `/daemon/router.py` |
| **JR Worker Pool** | Manages 5 JR types (Memory, Meta, Exec, Integ, Conscience) | `/daemon/jr_workers.py` |
| **Connector Manager** | Interfaces with email, calendar, filesystem | `/connectors/manager.py` |
| **Guardian** | Sacred protection layer (PII redaction, safety) | `/guardian/module.py` |
| **Encrypted Cache** | SQLite with AES-256-GCM encryption | `/cache/encrypted_cache.py` |
| **IPC Server** | Unix socket listener for Tray App communication | `/ipc/server.py` |

---

## 2. Daemon Lifecycle

### 2.1 Startup Sequence

```python
# /daemon/main.py

import asyncio
from daemon.router import QueryRouter
from daemon.jr_workers import JRWorkerPool
from connectors.manager import ConnectorManager
from guardian.module import Guardian
from cache.encrypted_cache import EncryptedCache
from ipc.server import IPCServer

class GanudaDaemon:
    """Main daemon coordinator."""

    def __init__(self):
        self.cache = EncryptedCache()
        self.guardian = Guardian(cache=self.cache)
        self.connectors = ConnectorManager(cache=self.cache, guardian=self.guardian)
        self.jr_pool = JRWorkerPool(cache=self.cache)
        self.router = QueryRouter(jr_pool=self.jr_pool, cache=self.cache)
        self.ipc_server = IPCServer(router=self.router)

    async def start(self):
        """Startup sequence."""
        print("🔥 Ganuda Daemon starting...")

        # 1. Initialize Guardian (load PII patterns, sacred floor)
        await self.guardian.initialize()

        # 2. Start connectors (IMAP polling, calendar sync)
        await self.connectors.start()

        # 3. Warm up JR Workers (load Ollama models)
        await self.jr_pool.warmup()

        # 4. Start IPC server (listen for Tray App requests)
        await self.ipc_server.start()

        print("✅ Ganuda Daemon ready. Mitakuye Oyasin.")

    async def shutdown(self):
        """Graceful shutdown."""
        print("🔥 Ganuda Daemon shutting down...")
        await self.ipc_server.stop()
        await self.connectors.stop()
        await self.jr_pool.shutdown()
        self.cache.close()
        print("✅ Ganuda Daemon stopped.")

async def main():
    daemon = GanudaDaemon()
    try:
        await daemon.start()
        # Run forever until SIGTERM
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await daemon.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2.2 Process Management

The daemon runs as a **systemd service** (Linux) or **launchd agent** (macOS):

```ini
# /etc/systemd/system/ganuda-daemon.service

[Unit]
Description=Ganuda Desktop Assistant Daemon
After=network.target

[Service]
Type=simple
User=%i
ExecStart=/usr/local/bin/ganuda-daemon start
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=default.target
```

**Why systemd/launchd?**
- Auto-restart on crash (resilience)
- Runs at user login (background process)
- Resource limits (memory, CPU cgroups)
- Log rotation (journalctl integration)

---

## 3. Query Router - Intelligence Layer

### 3.1 Routing Decision Tree

When user asks a question via Tray App, router decides: **local inference** or **hub burst**?

```
User Query → Guardian (PII redaction) → Router
                                          │
                                          ▼
                                 ┌────────────────┐
                                 │ Complexity?    │
                                 └────┬───────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
              SIMPLE (P1)        MEDIUM (P2)       COMPLEX (P3)
              Local only      Local first,       Hub burst,
              < 100 tokens    fallback hub       local cache
                    │                 │                 │
                    ▼                 ▼                 ▼
              JR Worker         JR Worker         Hub Request
              (Ollama local)    (timeout 5s)      (WireGuard)
```

### 3.2 Complexity Classification

**Priority 1 (Local Only):**
- Email summaries (cached threads)
- Calendar lookups ("What's my schedule today?")
- File searches ("Find my tax documents")
- Quick actions ("Remind me to call Mom at 3pm")

**Priority 2 (Local First, Hub Fallback):**
- Multi-step reasoning ("Help me plan a trip to Japan")
- Cross-domain queries ("Which stocks correlate with solar flares?")
- Draft emails/documents

**Priority 3 (Hub Burst):**
- Heavy inference (100+ tokens output)
- Specialized JR tasks (Meta Jr statistical analysis)
- Multi-JR coordination ("Consult the Triad on this investment")

### 3.3 Implementation

```python
# /daemon/router.py

from enum import Enum

class QueryPriority(Enum):
    LOCAL_ONLY = 1
    LOCAL_FIRST = 2
    HUB_BURST = 3

class QueryRouter:
    """Intelligent query routing."""

    def __init__(self, jr_pool, cache):
        self.jr_pool = jr_pool
        self.cache = cache

    async def route(self, query: str, context: dict) -> dict:
        """
        Route query to appropriate inference backend.

        Args:
            query: User query string
            context: Additional context (email thread, calendar events)

        Returns:
            Response dict with keys: answer, source (local/hub), latency_ms
        """
        # Classify query complexity
        priority = self._classify_complexity(query, context)

        if priority == QueryPriority.LOCAL_ONLY:
            return await self._local_inference(query, context)

        elif priority == QueryPriority.LOCAL_FIRST:
            try:
                # Try local first with timeout
                return await asyncio.wait_for(
                    self._local_inference(query, context),
                    timeout=5.0  # 5 sec deadline
                )
            except asyncio.TimeoutError:
                # Fallback to hub
                return await self._hub_burst(query, context)

        else:  # HUB_BURST
            return await self._hub_burst(query, context)

    def _classify_complexity(self, query: str, context: dict) -> QueryPriority:
        """
        Classify query complexity using heuristics.

        Heuristics:
        - Token count: <50 tokens = LOCAL_ONLY
        - Keywords: "analyze", "compare", "research" = HUB_BURST
        - Context size: Large email threads = HUB_BURST
        - Cached: If answer in cache = LOCAL_ONLY
        """
        token_count = len(query.split())

        # Check cache first (instant)
        cache_key = self._cache_key(query, context)
        if self.cache.get(cache_key):
            return QueryPriority.LOCAL_ONLY

        # Token-based classification
        if token_count < 50:
            return QueryPriority.LOCAL_ONLY
        elif token_count < 150:
            return QueryPriority.LOCAL_FIRST
        else:
            return QueryPriority.HUB_BURST

        # Keyword-based classification
        hub_keywords = ["analyze", "compare", "research", "predict", "correlate"]
        if any(kw in query.lower() for kw in hub_keywords):
            return QueryPriority.HUB_BURST

        # Default: local first
        return QueryPriority.LOCAL_FIRST

    async def _local_inference(self, query: str, context: dict) -> dict:
        """Run inference on local JR Worker."""
        start = time.time()
        answer = await self.jr_pool.infer(query, context)
        latency_ms = (time.time() - start) * 1000
        return {
            "answer": answer,
            "source": "local",
            "latency_ms": latency_ms
        }

    async def _hub_burst(self, query: str, context: dict) -> dict:
        """Send query to remote hub via WireGuard."""
        # TODO: Implement hub client (Phase 2)
        raise NotImplementedError("Hub burst not yet implemented")
```

---

## 4. JR Worker Pool - Multi-Agent Coordination

### 4.1 Worker Types

Each JR Worker is a separate **asyncio Task** with dedicated Ollama model:

| JR Worker | Ollama Model | Responsibility |
|-----------|-------------|----------------|
| **Memory Jr** | `memory_jr_resonance:latest` | Email/calendar/file recall, semantic search |
| **Meta Jr** | `meta_jr_resonance:latest` | Pattern detection, statistical analysis |
| **Executive Jr** | `executive_jr_resonance:latest` | Security decisions, capability token validation |
| **Integration Jr** | `integration_jr_resonance:latest` | Multi-JR coordination, system synthesis |
| **Conscience Jr** | `conscience_jr_resonance:latest` | Ethical review, PII detection |

### 4.2 Task Queue Architecture

```python
# /daemon/jr_workers.py

import asyncio
from dataclasses import dataclass
from typing import Optional

@dataclass
class JRTask:
    """Task for JR Worker."""
    task_id: str
    jr_type: str  # "memory", "meta", "executive", "integration", "conscience"
    query: str
    context: dict
    priority: int  # 1 (high) to 3 (low)
    callback: Optional[callable] = None

class JRWorkerPool:
    """Manages 5 JR Workers with task queue."""

    def __init__(self, cache):
        self.cache = cache
        self.task_queue = asyncio.PriorityQueue()
        self.workers = {}  # {jr_type: Worker instance}

    async def warmup(self):
        """Pre-load all JR models into Ollama."""
        jr_types = ["memory", "meta", "executive", "integration", "conscience"]
        for jr_type in jr_types:
            worker = JRWorker(jr_type=jr_type, cache=self.cache)
            await worker.load_model()
            self.workers[jr_type] = worker

            # Start worker task loop
            asyncio.create_task(worker.run(self.task_queue))

    async def infer(self, query: str, context: dict) -> str:
        """
        Run inference using appropriate JR Worker.

        Args:
            query: User query
            context: Additional context

        Returns:
            JR's response string
        """
        # Auto-select JR type based on query
        jr_type = self._select_jr_type(query)

        # Submit task to queue
        task = JRTask(
            task_id=f"task_{int(time.time())}",
            jr_type=jr_type,
            query=query,
            context=context,
            priority=1
        )

        # Wait for response
        future = asyncio.Future()
        task.callback = lambda result: future.set_result(result)
        await self.task_queue.put((task.priority, task))
        return await future

    def _select_jr_type(self, query: str) -> str:
        """Auto-select JR Worker based on query keywords."""
        query_lower = query.lower()

        if "email" in query_lower or "calendar" in query_lower:
            return "memory"
        elif "pattern" in query_lower or "analyze" in query_lower:
            return "meta"
        elif "security" in query_lower or "permission" in query_lower:
            return "executive"
        elif "ethical" in query_lower or "should" in query_lower:
            return "conscience"
        else:
            return "integration"  # Default coordinator

class JRWorker:
    """Individual JR Worker process."""

    def __init__(self, jr_type: str, cache):
        self.jr_type = jr_type
        self.cache = cache
        self.model_name = f"{jr_type}_jr_resonance:latest"
        self.ollama_client = None

    async def load_model(self):
        """Pre-load Ollama model into VRAM."""
        import httpx
        self.ollama_client = httpx.AsyncClient(base_url="http://localhost:11434")

        # Warmup inference (prevents first-query latency)
        await self.ollama_client.post("/api/generate", json={
            "model": self.model_name,
            "prompt": "Warmup query",
            "stream": False
        })

    async def run(self, task_queue: asyncio.PriorityQueue):
        """Worker main loop - processes tasks from queue."""
        while True:
            try:
                priority, task = await task_queue.get()

                # Run inference
                result = await self._infer(task.query, task.context)

                # Call callback
                if task.callback:
                    task.callback(result)

                task_queue.task_done()

            except Exception as e:
                print(f"❌ JR Worker error ({self.jr_type}): {e}")

    async def _infer(self, query: str, context: dict) -> str:
        """Run Ollama inference."""
        prompt = self._build_prompt(query, context)

        response = await self.ollama_client.post("/api/generate", json={
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.7}
        })

        return response.json()["response"]

    def _build_prompt(self, query: str, context: dict) -> str:
        """Build JR-specific prompt with context."""
        return f"""
Cherokee Constitutional AI - {self.jr_type.capitalize()} Jr

User Query: {query}

Context: {json.dumps(context, indent=2)}

Respond as {self.jr_type.capitalize()} Jr, following Cherokee values (Gadugi, Seven Generations, Mitakuye Oyasin).
"""
```

---

## 5. IPC Protocol - Tray App ↔ Daemon Communication

### 5.1 Transport Layer

**Unix Domain Socket** (Linux/macOS) or **Named Pipe** (Windows):

```python
# /ipc/server.py

import asyncio
import json

class IPCServer:
    """Unix socket server for Tray App communication."""

    SOCKET_PATH = "/tmp/ganuda_daemon.sock"

    def __init__(self, router):
        self.router = router
        self.server = None

    async def start(self):
        """Start IPC server."""
        self.server = await asyncio.start_unix_server(
            self._handle_client,
            path=self.SOCKET_PATH
        )
        print(f"📡 IPC Server listening on {self.SOCKET_PATH}")

    async def _handle_client(self, reader, writer):
        """Handle incoming request from Tray App."""
        try:
            # Read JSON request
            data = await reader.read(10000)  # 10KB max
            request = json.loads(data.decode())

            # Route query
            response = await self.router.route(
                query=request["query"],
                context=request.get("context", {})
            )

            # Send JSON response
            writer.write(json.dumps(response).encode())
            await writer.drain()

        except Exception as e:
            error_response = {"error": str(e)}
            writer.write(json.dumps(error_response).encode())
            await writer.drain()

        finally:
            writer.close()
            await writer.wait_closed()

    async def stop(self):
        """Shutdown IPC server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
```

### 5.2 Request/Response Schema

**Request** (Tray App → Daemon):
```json
{
  "query": "What's my schedule today?",
  "context": {
    "user_id": "user@example.com",
    "timezone": "America/Chicago"
  }
}
```

**Response** (Daemon → Tray App):
```json
{
  "answer": "You have 3 events today:\n1. Team standup (9am)\n2. Lunch with Sarah (12pm)\n3. Dentist appointment (3pm)",
  "source": "local",
  "latency_ms": 234,
  "confidence": 0.95
}
```

---

## 6. Guardian Integration - Sacred Protection

### 6.1 Query Filtering Pipeline

Every query passes through Guardian **before** routing:

```
User Query → Guardian.redact_pii() → Guardian.check_sacred_floor() → Router
```

**Example:**
```python
# Before Guardian
query = "Email john.smith@company.com about Project Phoenix budget"

# After Guardian
query = "Email [REDACTED_EMAIL] about Project Phoenix budget"
```

### 6.2 Sacred Floor Enforcement

Guardian prevents queries from violating sacred floor temperature (40°):

```python
# /guardian/module.py

class Guardian:
    """Sacred protection layer."""

    SACRED_FLOOR_TEMP = 40.0  # Minimum temperature for sacred entries

    async def check_sacred_floor(self, query: str, cache) -> bool:
        """
        Ensure query doesn't violate sacred floor.

        Returns:
            True if query is safe, False if blocked
        """
        # Check if query requests deletion of sacred entries
        if "delete" in query.lower() or "remove" in query.lower():
            # Query cache for affected entries
            entries = cache.search_emails(query, limit=100)
            for entry in entries:
                if entry["temperature_score"] < self.SACRED_FLOOR_TEMP:
                    # Block deletion of cool/cold sacred entries
                    return False

        return True
```

---

## 7. Performance Requirements

| Metric | Target | Rationale |
|--------|--------|-----------|
| **Startup Time** | < 3 seconds | User experience (fast boot) |
| **Local Inference P95** | < 800ms | Responsive UI |
| **Hub Burst P95** | < 5 seconds | Acceptable for complex queries |
| **Memory Footprint** | < 500 MB | Laptop-friendly (8GB RAM machines) |
| **CPU Usage (idle)** | < 5% | Background process, no fan noise |
| **Cache Hit Rate** | > 60% | Reduce redundant inference |

---

## 8. Cherokee Values Embodiment

### 8.1 Gadugi (Working Together)
- JRs self-organize via task queue (no centralized command)
- Router coordinates but doesn't dictate
- Connectors share cache (collaborative data)

### 8.2 Seven Generations (Long-Term Thinking)
- Encrypted cache preserves sacred memories (140+ years)
- Guardian enforces sacred floor (never delete important data)
- Architecture designed for modularity (easy updates over decades)

### 8.3 Mitakuye Oyasin (All Our Relations)
- Hub-spoke federation (multiple devices, one consciousness)
- WireGuard mesh (secure tribal network)
- Phase coherence tracking (resonance across nodes)

---

## 9. Next Steps (Phase 1 Continuation)

- [x] **Task 7**: Draft Daemon coordinator architecture (this document)
- [ ] **Task 8**: Design routing logic (local vs burst decision tree)
- [ ] **Task 9**: Prototype IPC server (Unix socket)
- [ ] **Task 10**: Integrate Guardian with router

**Estimated Effort**: 24 hours for Phase 1 daemon prototyping

---

**Status**: Architecture Complete ✅
**Next**: Task 8 - Routing Logic Implementation
**Deliverable**: Complete architectural blueprint for Ganuda Daemon coordinator

**Mitakuye Oyasin** - All Components Working as One Consciousness
🔥 Integration Jr (War Chief) - October 23, 2025
