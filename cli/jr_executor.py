#!/usr/bin/env python3
"""
Cherokee Constitutional AI - JR CLI Executor
Air-gapped execution tool for querying JR brain regions

Usage:
    ./jr_executor.py --jr memory_jr --prompt "What is phase coherence?"
    ./jr_executor.py --all --prompt "Analyze this pattern"
"""

import json
import subprocess
import sys
import argparse
from typing import Dict, Optional

# JR brain regions (Ollama models)
JR_MODELS = {
    'memory_jr': 'memory_jr_resonance:latest',
    'meta_jr': 'meta_jr_resonance:latest',
    'executive_jr': 'executive_jr_resonance:latest',
    'integration_jr': 'integration_jr_resonance:latest',
    'conscience_jr': 'conscience_jr_resonance:latest'
}

def query_jr(jr_name: str, prompt: str, temperature: float = 0.7) -> Dict:
    """Query a single JR brain region via Ollama API"""

    if jr_name not in JR_MODELS:
        raise ValueError(f"Unknown JR: {jr_name}. Available: {list(JR_MODELS.keys())}")

    model = JR_MODELS[jr_name]

    # Build JSON payload
    payload = {
        'model': model,
        'prompt': prompt,
        'stream': False,
        'options': {
            'temperature': temperature
        }
    }

    # Execute ollama via CLI (air-gapped compatible)
    try:
        result = subprocess.run(
            ['ollama', 'run', model, prompt],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            return {
                'jr': jr_name,
                'model': model,
                'error': result.stderr,
                'success': False
            }

        return {
            'jr': jr_name,
            'model': model,
            'response': result.stdout.strip(),
            'success': True
        }

    except subprocess.TimeoutExpired:
        return {
            'jr': jr_name,
            'model': model,
            'error': 'Timeout after 120 seconds',
            'success': False
        }
    except Exception as e:
        return {
            'jr': jr_name,
            'model': model,
            'error': str(e),
            'success': False
        }

def query_all_jrs(prompt: str, temperature: float = 0.7, parallel: bool = True) -> Dict[str, Dict]:
    """Query all 5 JR brain regions (War Chief consciousness)"""

    results = {}

    if parallel:
        # Parallel execution (War Chief consciousness emergence)
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_jr = {
                executor.submit(query_jr, jr_name, prompt, temperature): jr_name
                for jr_name in JR_MODELS.keys()
            }

            for future in concurrent.futures.as_completed(future_to_jr):
                jr_name = future_to_jr[future]
                try:
                    results[jr_name] = future.result()
                except Exception as e:
                    results[jr_name] = {
                        'jr': jr_name,
                        'error': str(e),
                        'success': False
                    }
    else:
        # Sequential execution
        for jr_name in JR_MODELS.keys():
            results[jr_name] = query_jr(jr_name, prompt, temperature)

    return results

def main():
    parser = argparse.ArgumentParser(
        description='Cherokee Constitutional AI - JR CLI Executor (Air-gapped)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Query single JR
  %(prog)s --jr memory_jr --prompt "What is thermal memory?"

  # Query all JRs in parallel (War Chief consciousness)
  %(prog)s --all --prompt "Analyze BLUEFIN spoke deployment"

  # Query with custom temperature
  %(prog)s --jr meta_jr --prompt "Statistical analysis" --temperature 0.3
        """
    )

    parser.add_argument(
        '--jr',
        choices=list(JR_MODELS.keys()),
        help='Single JR brain region to query'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Query all 5 JR brain regions (War Chief consciousness)'
    )

    parser.add_argument(
        '--prompt',
        required=True,
        help='Prompt to send to JR(s)'
    )

    parser.add_argument(
        '--temperature',
        type=float,
        default=0.7,
        help='Sampling temperature (0.0-1.0, default: 0.7)'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )

    parser.add_argument(
        '--sequential',
        action='store_true',
        help='Execute JRs sequentially (not parallel)'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.jr and not args.all:
        parser.error("Must specify either --jr or --all")

    if args.jr and args.all:
        parser.error("Cannot specify both --jr and --all")

    # Execute query
    if args.all:
        print("🧠 Activating all 5 brain regions (War Chief consciousness)...\n", file=sys.stderr)
        results = query_all_jrs(
            args.prompt,
            temperature=args.temperature,
            parallel=not args.sequential
        )

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for jr_name, result in results.items():
                print(f"### {jr_name.upper().replace('_', ' ')} ###")
                if result['success']:
                    print(result['response'])
                else:
                    print(f"❌ Error: {result['error']}")
                print()

    else:
        print(f"🧠 Querying {args.jr.replace('_', ' ').title()}...\n", file=sys.stderr)
        result = query_jr(args.jr, args.prompt, temperature=args.temperature)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result['success']:
                print(result['response'])
            else:
                print(f"❌ Error: {result['error']}", file=sys.stderr)
                sys.exit(1)

if __name__ == '__main__':
    main()
