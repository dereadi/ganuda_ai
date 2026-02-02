from enum import Enum

class MemoryType(Enum):
    EPISODIC = "episodic"    # Specific experiences: "Jr completed task X"
    SEMANTIC = "semantic"     # Extracted patterns: "Users prefer wizard flow"
    PROCEDURAL = "procedural" # How-to: "Deploy with: ansible-playbook..."
