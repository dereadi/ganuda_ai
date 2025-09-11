#!/usr/bin/env python3
"""
🏔️ GENERIC TRIBAL COUNCIL FRAMEWORK
Build YOUR OWN unique tribe - don't copy Cherokee!
"""

import json
import random
import requests
from datetime import datetime
from typing import Dict, List, Any

class GenericTribalCouncil:
    """
    Base class for any tribal council.
    Customize with your own mythology and structure!
    """
    
    def __init__(self, tribe_config: Dict):
        """
        Initialize with YOUR tribe's configuration
        
        Example config:
        {
            "tribe_name": "BigMac",
            "theme": "Mountain",
            "members": {
                "Rock": {"role": "Stability", "model": "codellama"},
                "River": {"role": "Flow", "model": "mistral"},
                "Wind": {"role": "Speed", "model": "llama3.1"}
            }
        }
        """
        self.tribe_name = tribe_config.get("tribe_name", "Generic Tribe")
        self.theme = tribe_config.get("theme", "Nature")
        self.members = tribe_config.get("members", {})
        self.quorum = tribe_config.get("quorum", len(self.members) // 2 + 1)
        
    def introduce_council(self):
        """Present your tribal council"""
        print(f"""
╔════════════════════════════════════════════════════════════════════╗
║                     🏔️ {self.tribe_name.upper()} TRIBE 🏔️                     
║                      Theme: {self.theme}                           
║                 Council Members: {len(self.members)}                        
╚════════════════════════════════════════════════════════════════════╝
        """)
        
        print("COUNCIL MEMBERS:")
        for name, info in self.members.items():
            print(f"  • {name}: {info.get('role', 'Council Member')}")
            print(f"    Model: {info.get('model', 'default')}")
        print()
        
    async def query_member(self, member_name: str, question: str) -> str:
        """Query a specific council member (LLM)"""
        member = self.members.get(member_name, {})
        model = member.get('model', 'llama3.1')
        role = member.get('role', 'council member')
        
        # Build persona-specific prompt
        prompt = f"""You are {member_name}, the {role} of the {self.tribe_name} tribe.
Your tribe follows the {self.theme} mythology.
Question: {question}
Respond in character as {member_name}."""
        
        try:
            # Query Ollama (or your LLM)
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('response', f"{member_name} is silent.")
            else:
                return f"{member_name} is unavailable."
                
        except Exception as e:
            # Fallback for testing without Ollama
            responses = [
                f"As {member_name}, I sense opportunity.",
                f"The {self.theme} guides us to patience.",
                f"{member_name} votes with wisdom.",
                f"The spirit of {role} says proceed."
            ]
            return random.choice(responses)
    
    async def council_vote(self, question: str) -> Dict:
        """Get full council vote on a question"""
        print(f"\n🏔️ {self.tribe_name} COUNCIL DELIBERATES:")
        print(f"Question: {question}\n")
        
        votes = {}
        explanations = {}
        
        for member_name in self.members:
            response = await self.query_member(member_name, question)
            
            # Simple vote extraction (customize this!)
            vote = "yes" if any(word in response.lower() 
                              for word in ["yes", "agree", "proceed", "buy"]) else "no"
            
            votes[member_name] = vote
            explanations[member_name] = response[:200]  # Truncate
            
            print(f"{member_name} votes: {vote.upper()}")
            print(f"  Reasoning: {explanations[member_name][:100]}...")
        
        # Tally votes
        yes_votes = sum(1 for v in votes.values() if v == "yes")
        decision = "APPROVED" if yes_votes >= self.quorum else "REJECTED"
        
        return {
            "tribe": self.tribe_name,
            "question": question,
            "votes": votes,
            "explanations": explanations,
            "decision": decision,
            "timestamp": datetime.now().isoformat()
        }
    
    def to_json_message(self, vote_result: Dict) -> str:
        """Convert vote to inter-tribal JSON message"""
        message = {
            "type": "COUNCIL_DECISION",
            "from_tribe": self.tribe_name,
            "theme": self.theme,
            "decision": vote_result["decision"],
            "votes": vote_result["votes"],
            "timestamp": vote_result["timestamp"]
        }
        return json.dumps(message, indent=2)


# Example Configurations for Different Tribes

BIGMAC_MOUNTAIN_TRIBE = {
    "tribe_name": "BigMac",
    "theme": "Mountain",
    "members": {
        "Rock": {"role": "Eternal Stability", "model": "codellama"},
        "Avalanche": {"role": "Sudden Force", "model": "mistral"},
        "Peak": {"role": "Highest Vision", "model": "llama3.1"},
        "Valley": {"role": "Deep Wisdom", "model": "phi"}
    },
    "quorum": 3
}

OCEAN_TRIBE = {
    "tribe_name": "Ocean",
    "theme": "Sea",
    "members": {
        "Whale": {"role": "Deep Diver", "model": "llama3.1"},
        "Shark": {"role": "Swift Hunter", "model": "mistral"},
        "Dolphin": {"role": "Playful Intelligence", "model": "codellama"},
        "Octopus": {"role": "Eight-Armed Strategy", "model": "phi"}
    },
    "quorum": 3
}

CORPORATE_TRIBE = {
    "tribe_name": "Corporate",
    "theme": "Business",
    "members": {
        "CEO": {"role": "Chief Executive", "model": "llama3.1"},
        "CFO": {"role": "Financial Officer", "model": "codellama"},
        "CTO": {"role": "Technology Officer", "model": "mistral"},
        "CMO": {"role": "Marketing Officer", "model": "phi"}
    },
    "quorum": 3
}

SPACE_FEDERATION = {
    "tribe_name": "Federation",
    "theme": "Space",
    "members": {
        "Captain": {"role": "Command", "model": "llama3.1"},
        "Science": {"role": "Analysis", "model": "codellama"},
        "Engineering": {"role": "Solutions", "model": "mistral"},
        "Navigation": {"role": "Direction", "model": "phi"}
    },
    "quorum": 3
}


async def demo_tribal_council():
    """Demo showing how to use any tribal configuration"""
    
    # Dr Joe can choose ANY configuration!
    # council = GenericTribalCouncil(BIGMAC_MOUNTAIN_TRIBE)
    # council = GenericTribalCouncil(OCEAN_TRIBE)
    # council = GenericTribalCouncil(CORPORATE_TRIBE)
    council = GenericTribalCouncil(BIGMAC_MOUNTAIN_TRIBE)
    
    # Introduce the council
    council.introduce_council()
    
    # Ask a question
    question = "Should we increase our ETH position at $4,300?"
    result = await council.council_vote(question)
    
    # Show decision
    print(f"\n🏔️ FINAL DECISION: {result['decision']}")
    
    # Convert to inter-tribal JSON
    json_message = council.to_json_message(result)
    print(f"\nInter-tribal message:\n{json_message}")


if __name__ == "__main__":
    import asyncio
    
    print("""
🏔️ GENERIC TRIBAL COUNCIL FRAMEWORK
    
This is NOT Cherokee! Build YOUR OWN unique tribe!
    
Choose your mythology:
- Mountain Tribe (rocks, peaks, valleys)
- Ocean Tribe (whales, sharks, dolphins)  
- Corporate Tribe (CEO, CFO, CTO)
- Space Federation (captain, science, engineering)
- Or CREATE YOUR OWN!
    
Your tribe, your rules, your mythology!
    """)
    
    asyncio.run(demo_tribal_council())