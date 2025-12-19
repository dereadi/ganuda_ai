#!/usr/bin/env python3
"""
Tribal Knowledge Base - Quick answers for common questions
These bypass the LLM when we have definitive answers
"""

TRIBAL_KNOWLEDGE = {
    # Repository / Setup questions
    "repository": """There isn't a public GitHub repo yet. The tribe code lives on redfin at /ganuda/.

To bootstrap your own tribe, copy from redfin via Tailscale:


Minimum requirements:
1. PostgreSQL with thermal_memory_archive table
2. Ollama with llama3.1:8b
3. LLM Gateway (FastAPI)""",

    "bootstrap": """See /ganuda/docs/DR_JOE_TRIBE_BOOTSTRAP_DEC17_2025.md for full guide.

Quick start:
1. Install PostgreSQL and Ollama
2. Copy /ganuda/services/llm_gateway from redfin
3. Run: python3 run_airgapped.py
4. Gateway will be on port 8080""",

    "tpm-macbook": """tpm-macbook (bmasass) is Darrell's M4 Max 128GB.
Air-gapped tribe setup at: /Users/Shared/ganuda/
Start with: /Users/Shared/ganuda/scripts/airgapped_startup.sh""",

    "bigmac": """BigMac is Dr. Joe's node at 192.168.132.242.
Bridge server: /ganuda/drjoe/cherokee_a2a_bridge.py (port 9001)
Client library: /ganuda/drjoe/bigmac_cherokee_client.py
Full docs: /ganuda/drjoe/BIGMAC_DEPLOYMENT_SUMMARY.md""",

    "nodes": """Cherokee AI Federation Nodes:
- redfin (192.168.132.223): Main server, vLLM, Gateway, SAG UI
- bluefin (192.168.132.222): PostgreSQL, thermal memory
- greenfin (192.168.132.224): Monitoring daemons
- sasass/sasass2: Mac Studios for edge dev
- tpm-macbook/bmasass: TPM command post (M4 Max)
- bigmac (192.168.132.242): Dr. Joe's node""",

    "gateway": """LLM Gateway runs on port 8080 (redfin) or 5000.
Endpoints:
- POST /v1/chat/completions - OpenAI compatible
- POST /v1/council/vote - 7-Specialist Council
- GET /health - Health check
Code: /ganuda/services/llm_gateway/gateway.py""",

    "council": """7-Specialist Council votes on decisions:
Crawdad (Security), Gecko (Performance), Turtle (Stability),
Hummingbird (UX), Owl (Strategy), Bear (Resources), Eagle (Vision)

Endpoint: POST /v1/council/vote
Metacognition: /ganuda/lib/metacognition/""",
}

def lookup_tribal_knowledge(question: str) -> str | None:
    """Check if question matches tribal knowledge"""
    q_lower = question.lower()
    
    # Check for keyword matches
    for keyword, answer in TRIBAL_KNOWLEDGE.items():
        if keyword in q_lower:
            return answer
    
    # Check for common patterns
    if any(w in q_lower for w in ['repo', 'github', 'clone', 'download']):
        return TRIBAL_KNOWLEDGE['repository']
    if any(w in q_lower for w in ['setup', 'install', 'start', 'build tribe']):
        return TRIBAL_KNOWLEDGE['bootstrap']
    if any(w in q_lower for w in ['which node', 'what nodes', 'infrastructure']):
        return TRIBAL_KNOWLEDGE['nodes']
    
    return None


if __name__ == '__main__':
    # Test
    test_questions = [
        "What repository should I use?",
        "How do I bootstrap a tribe on bigmac?",
        "What is tpm-macbook?",
        "How does the council work?",
    ]
    for q in test_questions:
        result = lookup_tribal_knowledge(q)
        print(f"Q: {q}")
        print(f"A: {result[:100] if result else 'No match'}...")
        print()
