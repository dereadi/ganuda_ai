# Jr Instructions: Agent-Kernel Microkernel Architecture

**Priority**: 2
**Assigned Jr**: it_triad_jr
**Source**: arXiv:2512.01610
**Ultrathink**: ULTRATHINK-AGENT-KERNEL-DEC20-2025.md

---

## OBJECTIVE

Refactor the LLM Gateway toward a microkernel architecture that separates core services from agent logic. This enables scaling to 10+ concurrent Jrs and cleaner separation of concerns.

---

### Task 1: Create Microkernel Core

Create `/ganuda/lib/federation_microkernel.py`:

```python
#!/usr/bin/env python3
"""
Federation Microkernel
Based on Agent-Kernel Architecture (arXiv:2512.01610)
Cherokee AI Federation - For Seven Generations
"""

import psycopg2
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from abc import ABC, abstractmethod
import threading
import queue

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}


class MessageRouter:
    """Route messages between registered agents."""

    def __init__(self):
        self.routes: Dict[str, Callable] = {}
        self.message_queue = queue.Queue()

    def register(self, agent_id: str, handler: Callable):
        """Register an agent's message handler."""
        self.routes[agent_id] = handler

    def unregister(self, agent_id: str):
        """Remove agent from routing table."""
        if agent_id in self.routes:
            del self.routes[agent_id]

    def route(self, from_agent: str, to_agent: str, message: dict) -> Optional[dict]:
        """Route message to target agent."""
        if to_agent not in self.routes:
            return {'error': f'Agent {to_agent} not found'}

        message['from'] = from_agent
        message['timestamp'] = datetime.now().isoformat()

        return self.routes[to_agent](message)

    def broadcast(self, from_agent: str, message: dict) -> Dict[str, dict]:
        """Broadcast message to all agents."""
        responses = {}
        for agent_id, handler in self.routes.items():
            if agent_id != from_agent:
                responses[agent_id] = handler(message)
        return responses


class MemoryManager:
    """Manage thermal memory access for agents."""

    def __init__(self):
        self._conn = None

    def _get_conn(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**DB_CONFIG)
        return self._conn

    def search(self, query: str, limit: int = 5) -> list:
        """Search thermal memory."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, LEFT(original_content, 200), current_stage, temperature_score
            FROM thermal_memory_archive
            WHERE original_content ILIKE %s
            ORDER BY temperature_score DESC, created_at DESC
            LIMIT %s
        """, (f'%{query}%', limit))
        results = cur.fetchall()
        cur.close()
        return results

    def write(self, content: str, stage: str = 'WHITE_HOT', score: int = 95) -> int:
        """Write to thermal memory."""
        import hashlib
        conn = self._get_conn()
        cur = conn.cursor()
        memory_hash = hashlib.md5(f"{content}_{datetime.now()}".encode()).hexdigest()
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (memory_hash, original_content, current_stage, temperature_score)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (memory_hash, content, stage, score))
        memory_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return memory_id

    def create_agent_context(self, agent_id: str):
        """Create isolated context for an agent."""
        # Future: Per-agent memory partitioning
        pass

    def archive_agent_context(self, agent_id: str):
        """Archive agent context before removal."""
        # Future: Persist agent state before cleanup
        pass


class TaskScheduler:
    """Manage Jr work queue."""

    def __init__(self):
        pass

    def _get_conn(self):
        return psycopg2.connect(**DB_CONFIG)

    def enqueue(self, task: dict, priority: int = 2) -> str:
        """Add task to Jr queue."""
        import hashlib
        conn = self._get_conn()
        cur = conn.cursor()
        task_id = hashlib.md5(f"{task['title']}_{datetime.now()}".encode()).hexdigest()
        cur.execute("""
            INSERT INTO jr_work_queue
            (task_id, title, assigned_jr, priority, status, instruction_file, created_at)
            VALUES (%s, %s, %s, %s, 'pending', %s, NOW())
            RETURNING task_id
        """, (task_id, task['title'], task.get('assigned_jr', 'it_triad_jr'),
              priority, task.get('instruction_file', '')))
        conn.commit()
        cur.close()
        conn.close()
        return task_id

    def get_pending(self, jr_type: str = None) -> list:
        """Get pending tasks."""
        conn = self._get_conn()
        cur = conn.cursor()
        if jr_type:
            cur.execute("""
                SELECT task_id, title, priority, created_at
                FROM jr_work_queue
                WHERE status = 'pending' AND assigned_jr = %s
                ORDER BY priority, created_at
            """, (jr_type,))
        else:
            cur.execute("""
                SELECT task_id, title, priority, assigned_jr, created_at
                FROM jr_work_queue
                WHERE status = 'pending'
                ORDER BY priority, created_at
            """)
        results = cur.fetchall()
        cur.close()
        conn.close()
        return results


class FederationMicrokernel:
    """Core microkernel for Cherokee AI Federation."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.memory = MemoryManager()
        self.scheduler = TaskScheduler()
        self.router = MessageRouter()
        self.agents: Dict[str, 'AgentModule'] = {}
        self._initialized = True

    def register_agent(self, agent: 'AgentModule'):
        """Register an agent with the kernel."""
        self.agents[agent.agent_id] = agent
        self.router.register(agent.agent_id, agent.handle_message)
        self.memory.create_agent_context(agent.agent_id)
        print(f"[KERNEL] Registered agent: {agent.agent_id}")

    def unregister_agent(self, agent_id: str):
        """Clean removal of an agent."""
        if agent_id in self.agents:
            self.memory.archive_agent_context(agent_id)
            self.router.unregister(agent_id)
            del self.agents[agent_id]
            print(f"[KERNEL] Unregistered agent: {agent_id}")

    def get_agent(self, agent_id: str) -> Optional['AgentModule']:
        """Get registered agent by ID."""
        return self.agents.get(agent_id)

    def list_agents(self) -> list:
        """List all registered agents."""
        return list(self.agents.keys())


class AgentModule(ABC):
    """Base class for all Federation agents."""

    def __init__(self, agent_id: str, kernel: FederationMicrokernel = None):
        self.agent_id = agent_id
        self.kernel = kernel or FederationMicrokernel()
        self.kernel.register_agent(self)

    @abstractmethod
    def handle_message(self, message: dict) -> dict:
        """Handle incoming message."""
        pass

    def send_message(self, to_agent: str, message: dict) -> dict:
        """Send message to another agent."""
        return self.kernel.router.route(self.agent_id, to_agent, message)

    def search_memory(self, query: str, limit: int = 5) -> list:
        """Search thermal memory."""
        return self.kernel.memory.search(query, limit)

    def write_memory(self, content: str, **kwargs) -> int:
        """Write to thermal memory."""
        return self.kernel.memory.write(content, **kwargs)

    def schedule_task(self, task: dict, priority: int = 2) -> str:
        """Schedule a task."""
        return self.kernel.scheduler.enqueue(task, priority)


# Example specialist implementation
class SpecialistAgent(AgentModule):
    """7-Specialist Council member."""

    def __init__(self, name: str, persona: str, kernel: FederationMicrokernel = None):
        super().__init__(f"specialist_{name}", kernel)
        self.name = name
        self.persona = persona

    def handle_message(self, message: dict) -> dict:
        """Process council query."""
        if message.get('type') == 'vote_request':
            return self.vote(message.get('question', ''))
        return {'status': 'unknown_message_type'}

    def vote(self, question: str) -> dict:
        """Generate vote on question."""
        # Placeholder - actual implementation calls vLLM
        return {
            'specialist': self.name,
            'vote': 'PROCEED',
            'reasoning': f'{self.name} perspective on: {question[:50]}...'
        }


if __name__ == '__main__':
    # Test the microkernel
    kernel = FederationMicrokernel()

    # Register test agents
    gecko = SpecialistAgent('gecko', 'Technical SME')
    crawdad = SpecialistAgent('crawdad', 'Security specialist')

    print(f"Registered agents: {kernel.list_agents()}")

    # Test message routing
    response = gecko.send_message('specialist_crawdad', {
        'type': 'vote_request',
        'question': 'Should we implement HiveMind contribution tracking?'
    })
    print(f"Response: {response}")
```

---

### Task 2: Create Jr Agent Implementation

Create `/ganuda/lib/jr_agent.py`:

```python
#!/usr/bin/env python3
"""
Jr Agent Module
Based on Agent-Kernel Architecture
Cherokee AI Federation - For Seven Generations
"""

from federation_microkernel import AgentModule, FederationMicrokernel
from datetime import datetime


class JrAgent(AgentModule):
    """Autonomous Jr worker agent."""

    def __init__(self, jr_type: str, kernel: FederationMicrokernel = None):
        super().__init__(f"jr_{jr_type}_{datetime.now().timestamp()}", kernel)
        self.jr_type = jr_type
        self.current_task = None
        self.completed_tasks = []

    def handle_message(self, message: dict) -> dict:
        """Handle Jr-specific messages."""
        msg_type = message.get('type')

        if msg_type == 'assign_task':
            return self.accept_task(message.get('task'))
        elif msg_type == 'status':
            return self.get_status()
        elif msg_type == 'complete':
            return self.complete_current_task(message.get('result'))

        return {'error': 'unknown_message_type'}

    def accept_task(self, task: dict) -> dict:
        """Accept a new task."""
        if self.current_task:
            return {'error': 'Already working on a task', 'current': self.current_task}

        self.current_task = task
        return {'status': 'accepted', 'task': task}

    def get_status(self) -> dict:
        """Get current Jr status."""
        return {
            'jr_id': self.agent_id,
            'jr_type': self.jr_type,
            'current_task': self.current_task,
            'completed_count': len(self.completed_tasks),
            'available': self.current_task is None
        }

    def complete_current_task(self, result: dict) -> dict:
        """Mark current task complete."""
        if not self.current_task:
            return {'error': 'No current task'}

        self.completed_tasks.append({
            'task': self.current_task,
            'result': result,
            'completed_at': datetime.now().isoformat()
        })
        completed = self.current_task
        self.current_task = None

        return {'status': 'completed', 'task': completed}


class JrScaler:
    """Dynamic Jr scaling based on queue depth."""

    def __init__(self, kernel: FederationMicrokernel, min_jrs: int = 1, max_jrs: int = 10):
        self.kernel = kernel
        self.min_jrs = min_jrs
        self.max_jrs = max_jrs
        self.active_jrs: dict = {}

    def evaluate_scaling(self) -> dict:
        """Determine if we need more or fewer Jrs."""
        pending = self.kernel.scheduler.get_pending()
        queue_depth = len(pending)
        current = len(self.active_jrs)

        # Target: 1 Jr per 3 pending tasks
        target = min(max(queue_depth // 3, self.min_jrs), self.max_jrs)

        action = None
        if target > current:
            action = f"scale_up_{target - current}"
        elif target < current:
            action = f"scale_down_{current - target}"

        return {
            'queue_depth': queue_depth,
            'current_jrs': current,
            'target_jrs': target,
            'action': action
        }

    def scale_up(self, count: int = 1):
        """Spin up additional Jrs."""
        for _ in range(count):
            jr = JrAgent('it_triad_jr', self.kernel)
            self.active_jrs[jr.agent_id] = jr
        return len(self.active_jrs)

    def scale_down(self, count: int = 1):
        """Remove idle Jrs."""
        idle = [jid for jid, jr in self.active_jrs.items()
                if jr.current_task is None]

        for jid in idle[:count]:
            self.kernel.unregister_agent(jid)
            del self.active_jrs[jid]

        return len(self.active_jrs)


if __name__ == '__main__':
    kernel = FederationMicrokernel()
    scaler = JrScaler(kernel)

    print(f"Scaling evaluation: {scaler.evaluate_scaling()}")

    # Scale up
    scaler.scale_up(3)
    print(f"After scale up: {kernel.list_agents()}")

    # Scale down idle
    scaler.scale_down(1)
    print(f"After scale down: {kernel.list_agents()}")
```

---

## SUCCESS CRITERIA

1. federation_microkernel.py created with all core services
2. jr_agent.py created with JrAgent and JrScaler
3. Agents can register/unregister with kernel
4. Message routing works between agents
5. JrScaler correctly calculates scaling decisions

---

*For Seven Generations - Cherokee AI Federation*
