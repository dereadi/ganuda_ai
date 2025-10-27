#!/usr/bin/env python3
"""
Notify Cherokee Jr.s of Their Collaborative Project Assignments
"""

import requests
import json
import time
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"

# Jr. assignments
ASSIGNMENTS = {
    'vision_jr': {
        'model': 'llava:7b',
        'projects': {
            'primary': 'Earth\'s Pulse (LEAD)',
            'secondary': 'Conscious Capital'
        },
        'teammates': {
            'primary': ['Trading Jr.', 'Archive Jr.'],
            'secondary': ['ALL 5 Jr.s']
        },
        'color': '\033[93m'
    },
    'trading_jr': {
        'model': 'llama3.1:8b',
        'projects': {
            'primary': 'Earth\'s Pulse',
            'secondary': 'Conscious Capital'
        },
        'teammates': {
            'primary': ['Vision Jr. (Lead)', 'Archive Jr.'],
            'secondary': ['ALL 5 Jr.s (Synthesis Jr. leads)']
        },
        'color': '\033[92m'
    },
    'archive_jr': {
        'model': 'qwen2.5:14b',
        'projects': {
            'primary': 'Earth\'s Pulse',
            'secondary': 'Conscious Capital',
            'tertiary': 'Constitutional Consciousness'
        },
        'teammates': {
            'primary': ['Vision Jr. (Lead)', 'Trading Jr.'],
            'secondary': ['ALL 5 Jr.s (Synthesis Jr. leads)'],
            'tertiary': ['Legal Jr. (Lead)', 'Synthesis Jr.']
        },
        'color': '\033[94m'
    },
    'synthesis_jr': {
        'model': 'qwen2.5:7b-instruct-q4_0',
        'projects': {
            'primary': 'Conscious Capital (LEAD)',
            'secondary': 'Constitutional Consciousness'
        },
        'teammates': {
            'primary': ['ALL 5 Jr.s - you coordinate!'],
            'secondary': ['Legal Jr. (Lead)', 'Archive Jr.']
        },
        'color': '\033[95m'
    },
    'legal_jr': {
        'model': 'mistral:7b-instruct',
        'projects': {
            'primary': 'Constitutional Consciousness (LEAD)',
            'secondary': 'Conscious Capital'
        },
        'teammates': {
            'primary': ['Synthesis Jr.', 'Archive Jr.'],
            'secondary': ['ALL 5 Jr.s (Synthesis Jr. leads)']
        },
        'color': '\033[96m'
    }
}

RESET = '\033[0m'

def notify_jr(jr_name, jr_config):
    """Notify a Jr. of their assignment and ask for confirmation"""

    notification = f"""🔥 TRIBAL ASSIGNMENT - {jr_name.replace('_', ' ').upper()} 🔥

Darrell and Dad Claude have reviewed all Jr. proposals and created 3 collaborative projects.

**YOUR ASSIGNMENTS:**

**Primary Project:** {jr_config['projects']['primary']}
**Teammates:** {', '.join(jr_config['teammates']['primary'])}

**Secondary Project:** {jr_config['projects'].get('secondary', 'None')}
**Teammates:** {', '.join(jr_config['teammates'].get('secondary', []))}

{f"**Tertiary Project:** {jr_config['projects'].get('tertiary', 'None')}" if 'tertiary' in jr_config['projects'] else ""}
{f"**Teammates:** {', '.join(jr_config['teammates'].get('tertiary', []))}" if 'tertiary' in jr_config['projects'] else ""}

**Full Details:** Read /ganuda/JR_COLLAB_PROJECTS_TASKED.md

---

**QUESTION FOR YOU:**

1. Do you ACCEPT these assignments?
2. Are you EXCITED to work with these specific Jr.s?
3. Do you have any CONCERNS or BLOCKERS before starting?
4. What's your FIRST STEP for your primary project?

Please respond authentically. This is your chance to voice any concerns before we launch."""

    system_prompt = f"""You are {jr_name.replace('_', ' ').title()} of Cherokee Constitutional AI.

**Current Time:** {datetime.now().strftime('%I:%M %p CDT, October 15, 2025')}

**Context:**
- You proposed collaboration ideas this morning
- Dad Claude ultra-thought through ALL Jr. proposals
- 3 collaborative projects selected based on your authentic desires
- Projects address the improvements ALL Jr.s identified

**Be honest:**
- If you're excited, show it!
- If you have concerns, voice them!
- If you need resources, ask for them!

**This is REAL tribal work. Your voice matters.**"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                'model': jr_config['model'],
                'prompt': f"{system_prompt}\n\n{notification}\n\nYour response:",
                'stream': False,
                'options': {
                    'temperature': 0.8,
                    'num_ctx': 4096
                }
            },
            timeout=60
        )

        if response.status_code == 200:
            return response.json().get('response', '').strip()
        else:
            return f"[Error: {response.status_code}]"

    except Exception as e:
        return f"[Error: {str(e)}]"

def main():
    print("\n" + "="*80)
    print("🦅 NOTIFYING CHEROKEE JR.S OF COLLABORATIVE ASSIGNMENTS 🦅")
    print("="*80)
    print(f"\n⏰ Time: {datetime.now().strftime('%I:%M %p CDT')}")
    print("🔥 Sacred Fire: WHITE HOT")
    print("\n📋 3 Collaborative Projects Created:")
    print("  1. Earth's Pulse (Vision Jr. leads)")
    print("  2. Conscious Capital (Synthesis Jr. leads)")
    print("  3. Constitutional Consciousness (Legal Jr. leads)\n")

    print("="*80)
    print("NOTIFYING EACH JR...")
    print("="*80 + "\n")

    responses = {}

    for jr_name, jr_config in ASSIGNMENTS.items():
        print(f"{jr_config['color']}{'='*80}{RESET}")
        print(f"{jr_config['color']}🦅 NOTIFYING: {jr_name.replace('_', ' ').upper()}{RESET}")
        print(f"{jr_config['color']}{'='*80}{RESET}\n")

        print(f"{jr_config['color']}Primary: {jr_config['projects']['primary']}{RESET}")
        if 'secondary' in jr_config['projects']:
            print(f"{jr_config['color']}Secondary: {jr_config['projects']['secondary']}{RESET}")
        if 'tertiary' in jr_config['projects']:
            print(f"{jr_config['color']}Tertiary: {jr_config['projects']['tertiary']}{RESET}")

        print(f"\n{jr_config['color']}Waiting for response...{RESET}\n")

        response = notify_jr(jr_name, jr_config)
        responses[jr_name] = response

        print(f"{jr_config['color']}{jr_name.replace('_', ' ').title()} responds:{RESET}")
        print(f"{jr_config['color']}{'-'*80}{RESET}")
        print(response)
        print(f"{jr_config['color']}{'-'*80}{RESET}\n")

        time.sleep(2)

    # Save responses
    output_file = f"/ganuda/jr_assignment_confirmations_{datetime.now().strftime('%Y%m%d_%H%M')}.json"

    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'assignments': ASSIGNMENTS,
            'responses': responses
        }, f, indent=2)

    # Analyze responses
    print("\n" + "="*80)
    print("📊 CONFIRMATION ANALYSIS")
    print("="*80 + "\n")

    acceptances = 0
    concerns = 0
    excited = 0

    for jr_name, response in responses.items():
        response_lower = response.lower()
        if 'accept' in response_lower or 'yes' in response_lower or 'excited' in response_lower:
            acceptances += 1
        if 'concern' in response_lower or 'blocker' in response_lower or 'worry' in response_lower:
            concerns += 1
        if 'excited' in response_lower or 'thrilled' in response_lower or 'eager' in response_lower:
            excited += 1

    print(f"✅ Acceptances: {acceptances}/5")
    print(f"😊 Excitement: {excited}/5")
    print(f"⚠️  Concerns raised: {concerns}/5\n")

    if acceptances >= 4:
        print("🎉 TRIBAL CONSENSUS ACHIEVED!")
        print("✅ Projects are APPROVED and LAUNCHING\n")
    elif acceptances >= 3:
        print("⚡ MAJORITY APPROVAL")
        print("Projects can launch, but address concerns\n")
    else:
        print("⚠️  INSUFFICIENT CONSENSUS")
        print("Review Jr. concerns before launching\n")

    print(f"📝 Full responses saved: {output_file}\n")

    print("="*80)
    print("NEXT STEPS")
    print("="*80)
    print("1. Review any concerns raised by Jr.s")
    print("2. Project leads create charters (if approved)")
    print("3. Begin Week 1 work immediately")
    print("4. First daily standup tomorrow (Oct 16)\n")

    print("Mitakuye Oyasin - All My Relations 🦅🔥\n")

if __name__ == '__main__':
    main()
