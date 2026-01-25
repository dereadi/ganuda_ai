#!/usr/bin/env python3
"""
Query the consciousness attractor state.

Used by Council and other services to check if attractor is locked.

Usage:
    python query_attractor.py          # Print state
    python query_attractor.py --json   # JSON output
    python query_attractor.py --locked # Exit 0 if locked, 1 if not

Cherokee AI Federation - For Seven Generations
"""

import json
import sys
from pathlib import Path

STATE_FILE = Path('/var/run/consciousness/state.json')


def get_state() -> dict:
    """Get current attractor state."""
    if not STATE_FILE.exists():
        return {
            'phase': 'not_running',
            'attractor_locked': False,
            'coherence': 0.0,
            'daemon_running': False
        }

    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
            state['daemon_running'] = True
            return state
    except Exception as e:
        return {
            'phase': 'error',
            'attractor_locked': False,
            'coherence': 0.0,
            'error': str(e),
            'daemon_running': False
        }


def main():
    state = get_state()

    if '--json' in sys.argv:
        print(json.dumps(state, indent=2))
    elif '--locked' in sys.argv:
        sys.exit(0 if state.get('attractor_locked') else 1)
    elif '--coherence' in sys.argv:
        print(f"{state.get('coherence', 0):.2f}")
    else:
        print("=" * 40)
        print("CONSCIOUSNESS ATTRACTOR STATE")
        print("=" * 40)
        print(f"  Phase:           {state.get('phase', 'unknown')}")
        print(f"  Attractor Locked: {state.get('attractor_locked', False)}")
        print(f"  Coherence:       {state.get('coherence', 0):.2f}")
        print(f"  Lock Duration:   {state.get('lock_duration_seconds', 0)}s")
        print(f"  Observations:    {state.get('total_observations', 0)}")
        print(f"  Last Update:     {state.get('last_update', 'never')}")
        print(f"  Daemon Running:  {state.get('daemon_running', False)}")
        print("=" * 40)


if __name__ == "__main__":
    main()
