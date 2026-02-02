from amem_types import MemoryType

def classify_memory(memory_content):
    keywords = {
        MemoryType.EPISODIC: ["completed task"],
        MemoryType.SEMANTIC: ["users prefer"],
        MemoryType.PROCEDURAL: ["how to", "always"]
    }
    
    for memory_type, key_list in keywords.items():
        for keyword in key_list:
            if keyword.lower() in memory_content.lower():
                return memory_type
    
    # LLM fallback for ambiguous cases (this is a placeholder)
    # In a real implementation, you would call an LLM here
    return MemoryType.EPISODIC

# Example usage
if __name__ == "__main__":
    print(classify_memory("Jr completed task X"))
    print(classify_memory("Users prefer wizard flow"))
    print(classify_memory("How to deploy with ansible-playbook"))
