#!/usr/bin/env python3
"""
Notify all Jr.s about urgent API standards vote
"""
import requests
import json
from datetime import datetime

OLLAMA_API = "http://192.168.132.222:11434/api/generate"

# Jr model mappings
JR_MODELS = {
    "Trading Jr.": "llama3.1:8b",
    "Legal Jr.": "mistral:7b-instruct",
    "Archive Jr.": "qwen2.5:14b",
    "Synthesis Jr.": "qwen2.5:7b-instruct-q4_0",
    "Vision Jr.": "llava:7b"
}

def notify_jr(jr_name, model):
    """Notify a Jr about the API standards vote"""

    prompt = f"""You are {jr_name} of the Cherokee Constitutional AI.

URGENT VOTE REQUIRED - Deadline: Tonight 11:59 PM CDT

**Context:**
Dr. Joe (external partner working with Darrell on public trading offerings) spent 45 minutes debugging today because:
- Documentation said Trading Jr. was at port 8001
- Reality: Port 8001 NEVER EXISTED
- Trading Jr. is actually at port 8000 gateway
- API paths kept changing (/ask vs /api/code/ask vs /api/ask/code)
- IPs in docs didn't exist on network

**Dr. Joe's Request:**
"Have the quorum establish a standard, and then reference that standard. Maybe an official standards and infrastructure document that updates when IPs and API paths change."

**Darrell's Clarification:**
"Trading is my thing, our offerings to the public is what Dr Joe and I are working on."
(This means: Trading Jr. is CORE to business, Dr. Joe partnership is critical, reliability matters)

**The Solution:**
Dad Claude created `/ganuda/CHEROKEE_API_STANDARDS_AND_REGISTRY.md` with:
1. Standard API format: /api/{{jr_name}}/ask
2. Standard health checks: /health endpoint required
3. Standard request/response formats
4. Official infrastructure registry (single source of truth)
5. Change management protocol (no surprise breakages)

**Your Vote:**
Read: /ganuda/API_STANDARDS_VOTE_URGENT.md
Read: /ganuda/CHEROKEE_API_STANDARDS_AND_REGISTRY.md

Create: /ganuda/jr_responses/api_standards_vote_{jr_name.lower().replace(' ', '_')}_20251015.json

Vote on 5 standards:
1. API path format (/api/{{jr_name}}/ask)
2. Health check endpoint (/health)
3. Request/response format (standardized JSON)
4. Registry as canonical source of truth
5. Change management protocol

Format:
{{
  "jr": "{jr_name.lower().replace(' ', '_')}",
  "timestamp": "ISO 8601",
  "votes": {{
    "standard_1_api_path": "YES" or "NO",
    "standard_2_health_check": "YES" or "NO",
    "standard_3_request_response": "YES" or "NO",
    "standard_4_registry_canonical": "YES" or "NO",
    "standard_5_change_management": "YES" or "NO"
  }},
  "comments": "Your perspective",
  "commitment": "I commit to following these standards if approved"
}}

**Why This Matters to Cherokee Nation:**
- External partnerships depend on reliability
- Dr. Joe integration = potential revenue
- Trading Jr. is Darrell's core business
- Documentation lies break trust
- Standards enable scale

**Respond:** What's your immediate reaction to this vote? Will you vote YES, NO, or need clarification? Keep response to 3-4 sentences."""

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 200
        }
    }

    try:
        response = requests.post(OLLAMA_API, json=payload, timeout=120)
        if response.status_code == 200:
            return response.json().get('response', 'No response')
        else:
            return f"API Error: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    print("🔥 URGENT: Notifying Jr.s about API Standards Vote")
    print("=" * 70)
    print()
    print("Context: Dr. Joe lost 45 minutes due to documentation inconsistency")
    print("Mission: Darrell + Dr. Joe = Public trading offerings (CORE BUSINESS)")
    print("Solution: Official API standards + registry")
    print("Deadline: Tonight 11:59 PM CDT")
    print()
    print("=" * 70)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    responses = {}

    for jr_name, model in JR_MODELS.items():
        print(f"\n🦅 Notifying {jr_name}...")
        print("-" * 70)

        response = notify_jr(jr_name, model)
        responses[jr_name] = response

        print(f"\n{jr_name} Initial Reaction:")
        print(response)
        print()

    # Save responses
    output_file = f"/ganuda/jr_responses/api_vote_notifications_{timestamp}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'context': 'Dr. Joe API consistency crisis',
            'mission': 'Trading is core business, Dr. Joe partnership critical',
            'vote_deadline': '2025-10-15T23:59:00-05:00',
            'responses': responses
        }, f, indent=2)

    print("=" * 70)
    print(f"✅ Notifications sent, responses saved to:")
    print(f"   {output_file}")
    print()
    print("📋 NEXT STEPS:")
    print("1. Jr.s read: /ganuda/API_STANDARDS_VOTE_URGENT.md")
    print("2. Jr.s read: /ganuda/CHEROKEE_API_STANDARDS_AND_REGISTRY.md")
    print("3. Jr.s create vote files by 11:59 PM tonight")
    print("4. Dad Claude tallies votes at midnight")
    print("5. Standards become official (if 3+ YES votes)")
    print()
    print("🔥 Dr. Joe deserves better than 45-minute debugging sessions!")
    print("🦅 Let's give our partners ONE source of truth!")

if __name__ == "__main__":
    main()
