#!/usr/bin/env python3
"""
Claude Code Helper: Thermal Memory Access for bmasass
Simplifies thermal memory operations for Claude Code instances
"""
import sys
import json
import os
sys.path.insert(0, '/Users/Shared/ganuda/lib')

from triad_thermal_memory_api import TriadMemoryAPI, AccessLevel

class ClaudeThermalMemory:
    """Simplified thermal memory interface for Claude Code on bmasass"""

    def __init__(self, config_path="/Users/Shared/ganuda/.thermal_memory/config.json"):
        # Load config
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.triad_name = self.config['spoke_identity']['triad_name']
        self.api = TriadMemoryAPI()

    def remember(self, content: str, temperature: float = 85.0, tags: list = None):
        """
        Store a memory in thermal memory.

        Temperature guide:
        - 100°C: CONSTITUTIONAL (use sparingly)
        - 95°C: SACRED (auto-shared to all triads)
        - 90°C: HIGH (important federation-wide info)
        - 85°C: PUBLIC (general information)
        - <85°C: LOCAL (triad-specific)
        """
        if tags is None:
            tags = []

        # Add bmasass tag automatically
        if "bmasass" not in tags:
            tags.append("bmasass")

        memory_id = self.api.write_memory(
            content=content,
            temperature=temperature,
            source_triad=self.triad_name,
            tags=tags,
            access_level=AccessLevel.PUBLIC if temperature >= 85 else AccessLevel.TRIAD_ONLY
        )
        return memory_id

    def recall(self, min_temp: float = 0.0, max_temp: float = 100.0,
               tags: list = None, source_triad: str = None, limit: int = 50):
        """
        Query thermal memories from bluefin hub.
        """
        return self.api.query_memories(
            requesting_triad=self.triad_name,
            min_temperature=min_temp,
            max_temperature=max_temp,
            tags=tags,
            source_triad=source_triad,
            limit=limit
        )

    def recall_sacred(self):
        """Get all sacred memories (>75°C)"""
        return self.api.get_sacred_memories(requesting_triad=self.triad_name)

    def recall_by_tags(self, tags: list, limit: int = 50):
        """Query memories by tags"""
        return self.recall(tags=tags, limit=limit)

    def close(self):
        """Close connection pool"""
        self.api.close()

# Example usage
if __name__ == "__main__":
    mem = ClaudeThermalMemory()

    # Store a memory
    mem_id = mem.remember(
        content="Example memory from Claude Code on bmasass laptop",
        temperature=85.0,
        tags=["example", "laptop", "test"]
    )
    print(f"Stored memory: {mem_id}")

    # Recall sacred memories
    sacred = mem.recall_sacred()
    print(f"\nFound {len(sacred)} sacred memories")

    mem.close()
