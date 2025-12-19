#!/usr/bin/env python3
"""
Cherokee IT Jr - Mission Parser
Parses mission content from thermal memory into executable format
"""

import json
import os
from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class Mission:
    id: str
    title: str
    instructions_file: Optional[str]
    tasks: List[str]
    priority: str
    complexity_score: Dict
    constitutional_note: Optional[str]
    raw_content: str

class MissionParser:
    def parse(self, mission_row: tuple) -> Mission:
        """Parse mission from thermal memory row"""
        mission_id, content, temperature, tags, created_at = mission_row

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Plain text mission
            return Mission(
                id=str(mission_id),
                title=content[:100] if content else 'Untitled',
                instructions_file=None,
                tasks=[content] if content else [],
                priority='medium',
                complexity_score={},
                constitutional_note=None,
                raw_content=content or ''
            )

        # Support both 'instructions' and 'instructions_file' keys
        instructions_path = data.get('instructions_file') or data.get('instructions')

        return Mission(
            id=str(mission_id),
            title=data.get('title', 'Untitled Mission'),
            instructions_file=instructions_path,
            tasks=data.get('tasks', []),
            priority=data.get('priority', 'medium'),
            complexity_score=data.get('complexity_score', {}),
            constitutional_note=data.get('constitutional_note'),
            raw_content=content
        )

    def load_instructions(self, mission: Mission) -> str:
        """Load full instructions from file if specified"""
        if mission.instructions_file:
            # Try multiple paths for cross-platform compatibility
            paths_to_try = [
                mission.instructions_file,
                mission.instructions_file.replace('/Users/Shared/ganuda', '/ganuda'),
                mission.instructions_file.replace('/ganuda', '/Users/Shared/ganuda'),
            ]

            for path in paths_to_try:
                if os.path.exists(path):
                    with open(path) as f:
                        return f.read()

        return mission.raw_content
