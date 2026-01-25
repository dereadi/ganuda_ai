# KB-XONSH-PILOT-DEC19-2025: Xonsh Shell Pilot on sasass2

## Summary
Successfully deployed Xonsh (Python-powered shell) on sasass2 Mac Studio.

## Key Learnings

### Python Version Requirements
- Xonsh v0.20+ requires Python 3.11+
- sasass has Python 3.9.6 (too old) - SKIP for now
- sasass2 has Python 3.14.2 via Homebrew - WORKS

### Installation Method
- Homebrew pip has PEP 668 restriction (externally-managed-environment)
- Solution: Use pipx for isolated installation
- Command: `/opt/homebrew/bin/pipx install 'xonsh[full]'`

### Database Integration
- psycopg2 not included in xonsh venv by default
- Solution: `pipx inject xonsh psycopg2-binary`

## Files Created
- `/Users/Shared/ganuda/lib/xontrib_cherokee.py` - Custom xontrib
- `/Users/Shared/ganuda/config/xonshrc` - Configuration
- `/Users/Shared/ganuda/scripts/install_xonsh.sh` - Installation script

## Cherokee Xontrib Commands
- `thermal_search(query)` - Search thermal memory
- `thermal_write(content)` - Write to thermal memory
- `jr_queue_status()` - Show Jr work queue
- `federation_health()` - Ping all nodes
- `msp_score()` - Calculate MSP

## Rollout Plan
1. Week 1: Pilot on sasass2 ✅ COMPLETE
2. Week 2: Evaluate and fix issues
3. Week 3: Upgrade Python on sasass, extend pilot
4. Week 4: Linux nodes

For Seven Generations.