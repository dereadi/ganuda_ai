#!/usr/bin/env python3
"""
Daily Standup Generator - Integration Jr
Cherokee Constitutional AI - JR Coordination System
Purpose: Query all 15 JRs (5 types × 3 nodes) and generate daily progress digest
"""

import yaml
import requests
from datetime import date, datetime
import os
from typing import Dict, List


# Configuration
JR_TYPES = ['memory', 'meta', 'executive', 'integration', 'conscience']
NODES = {
    'redfin': 'localhost',      # War Chief
    'bluefin': 'bluefin',       # Peace Chief
    'sasass2': 'sasass2'        # Medicine Woman
}
OLLAMA_PORT = 11434


def query_jr_progress(jr_type: str, node_name: str, node_host: str) -> Dict:
    """Query a single JR for daily progress via Ollama API"""

    prompt = f"""# Daily Standup - {jr_type.title()} Jr on {node_name.upper()}

**Date**: {date.today().isoformat()}

Report your progress on Week 2 tasks in this format:
- Task: [your self-selected task]
- Progress: [percentage 0-100%]
- Metrics: [any quantitative progress metrics]
- Blockers: [none or describe blockers]
- Handoff: [what you need from other JRs or Chiefs]

Keep response to 3-4 sentences."""

    try:
        response = requests.post(
            f'http://{node_host}:{OLLAMA_PORT}/api/generate',
            json={
                'model': f'{jr_type}_jr_resonance:latest',
                'prompt': prompt,
                'stream': False,
                'options': {'temperature': 0.7}
            },
            timeout=60
        )

        jr_response = response.json().get('response', 'No response')

        return {
            'jr': jr_type,
            'node': node_name,
            'chief': 'war' if node_name == 'redfin' else ('peace' if node_name == 'bluefin' else 'medicine'),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'status': 'active',
            'report': jr_response
        }

    except Exception as e:
        return {
            'jr': jr_type,
            'node': node_name,
            'chief': 'war' if node_name == 'redfin' else ('peace' if node_name == 'bluefin' else 'medicine'),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'status': 'error',
            'error': str(e)
        }


def compile_daily_digest() -> Dict:
    """Query all 15 JRs and compile into daily digest"""

    print("🔥 Ganuda Daily Standup - Cherokee Constitutional AI")
    print("=" * 70)
    print(f"Date: {date.today().isoformat()}")
    print(f"Querying 15 JRs (5 types × 3 Chiefs)...\n")

    digest = {
        'date': date.today().isoformat(),
        'jr_reports': []
    }

    # Query each JR on each node
    for jr_type in JR_TYPES:
        for node_name, node_host in NODES.items():
            chief_name = 'War Chief' if node_name == 'redfin' else ('Peace Chief' if node_name == 'bluefin' else 'Medicine Woman')
            print(f"  Querying {jr_type.title()} Jr ({chief_name})...", end=' ')

            jr_report = query_jr_progress(jr_type, node_name, node_host)
            digest['jr_reports'].append(jr_report)

            status_icon = '✅' if jr_report['status'] == 'active' else '❌'
            print(f"{status_icon}")

    print(f"\n{'=' * 70}")
    print(f"✅ Daily standup complete: {len(digest['jr_reports'])} JRs reported\n")

    return digest


def save_daily_digest(digest: Dict, output_dir: str = './reports'):
    """Save daily digest to YAML file"""

    os.makedirs(output_dir, exist_ok=True)

    # Filename: daily_standup_YYYY-MM-DD.yaml
    filename = f"{output_dir}/daily_standup_{date.today().isoformat()}.yaml"

    with open(filename, 'w') as f:
        yaml.dump(digest, f, default_flow_style=False, sort_keys=False)

    print(f"📄 Daily digest saved: {filename}")

    # Also save as latest.yaml for easy reference
    latest_file = f"{output_dir}/daily_standup_latest.yaml"
    with open(latest_file, 'w') as f:
        yaml.dump(digest, f, default_flow_style=False, sort_keys=False)

    print(f"📄 Latest digest: {latest_file}\n")

    return filename


def main():
    """Main entry point for daily standup generator"""

    # Compile digest from all 15 JRs
    digest = compile_daily_digest()

    # Save to YAML files
    output_file = save_daily_digest(digest)

    print("Mitakuye Oyasin - All 15 JRs reporting for duty 🦅🕊️🌿\n")

    return output_file


if __name__ == '__main__':
    main()
