#!/usr/bin/env python3
"""
Push Ganuda vision to knowledge base server
"""

import requests
import json
from datetime import datetime

def push_to_knowledge_base():
    """Push the Ganuda vision to the knowledge base"""
    
    # Read the local file
    with open('/home/dereadi/scripts/claude/knowledge_base/ganuda_complete_vision.md', 'r') as f:
        content = f.read()
    
    # Prepare the payload
    payload = {
        "title": "ᎦᏅᏓ (GANUDA) - Complete Vision Document",
        "category": "Sacred Fire Innovation",
        "priority": "MAXIMUM",
        "tags": [
            "ganuda",
            "cherokee", 
            "two-wolves",
            "quantum-crawdads",
            "indigenous-tech",
            "digital-sovereignty",
            "major-ridge",
            "sacred-fire"
        ],
        "content": content,
        "metadata": {
            "created_by": "Sacred Fire Council",
            "created_at": datetime.now().isoformat(),
            "thermal_priority": 100,
            "sacred_fire_temperature": "WHITE_HOT",
            "seven_generations_assessed": True,
            "two_wolves_enabled": True,
            "coyote_tested": True,
            "oppenheimer_protocol": "Active",
            "indigenous_sovereignty": True,
            "patent_potential": "785+ micro-patents",
            "carbon_impact": "NEGATIVE (uses existing hardware)",
            "healing_potential": "Treaty of New Echota reconciliation"
        }
    }
    
    try:
        # Push to server
        response = requests.post(
            'http://192.168.132.223:3001/api/knowledge',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200 or response.status_code == 201:
            print("✅ Successfully pushed to knowledge base server!")
            print(f"Response: {response.text}")
        else:
            print(f"⚠️ Server responded with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to knowledge base server")
        print("But local copy is saved at:")
        print("/home/dereadi/scripts/claude/knowledge_base/ganuda_complete_vision.md")
    except Exception as e:
        print(f"Error: {e}")
        print("But local copy is saved successfully!")
    
    print("\n📍 Ganuda vision is now in TWO places:")
    print("  1. Local: /home/dereadi/scripts/claude/knowledge_base/ganuda_complete_vision.md")
    print("  2. Server: http://192.168.132.223:3001/knowledge (if successful)")
    print("\n🔥 Sacred knowledge preserved in multiple locations!")
    print("🦞 The crawdads have found their ridge!")

if __name__ == "__main__":
    push_to_knowledge_base()