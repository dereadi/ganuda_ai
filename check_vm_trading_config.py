#!/usr/bin/env python3
"""
Check and optimize VM trading bot configuration
"""

import subprocess
import json
import os

print("🔍 VM TRADING CONFIGURATION ANALYSIS")
print("=" * 60)

# Check container-based trading services
print("\n📦 CONTAINER-BASED TRADING:")
result = subprocess.run(['podman', 'ps', '--format', 'json'], capture_output=True, text=True)
if result.returncode == 0:
    containers = json.loads(result.stdout)
    trading_containers = []
    for container in containers:
        if any(term in container.get('Names', [''])[0].lower() for term in ['trade', 'bot', 'crawdad', 'specialist']):
            trading_containers.append(container['Names'][0])
    
    if trading_containers:
        print(f"Found {len(trading_containers)} trading containers:")
        for name in trading_containers:
            print(f"  - {name}")
    else:
        print("  No trading containers currently running")
else:
    print("  Error checking containers")

# Check Cherokee AI trading integration
print("\n🦅 CHEROKEE AI TRADING INTEGRATION:")
cherokee_services = [
    ('Cherokee War Chief', 'http://localhost:12001', 'Ollama LLM for decisions'),
    ('Cherokee Elder Council', 'http://localhost:4100', 'Council voting system'),
    ('Cherokee Unified API', 'http://localhost:4000', 'Trading API gateway')
]

for name, url, desc in cherokee_services:
    print(f"  {name}: {desc}")
    print(f"    Endpoint: {url}")

# Suggested VM-based trading architecture
print("\n💡 RECOMMENDED VM TRADING ARCHITECTURE:")
print("""
1. CONTAINERIZED SPECIALIST ARMY:
   - Create Docker/Podman containers for each specialist
   - Deploy inside cherokee-cloud-environment
   - Use Cherokee Elder Council for consensus

2. CONFIGURATION TWEAKS NEEDED:
   - Move from file-based to container-based deployment
   - Use Cherokee Unified API (port 4000) for all trades
   - Integrate with Elder Council (port 4100) for decisions
   - Store state in cherokee-postgres-17-redfin

3. MODEL OPTIMIZATIONS:
   - Use Cherokee War Chief LLM for market analysis
   - Implement distributed consensus voting
   - Store thermal memories in PostgreSQL
   - Use Podman networking for inter-container communication

4. DEPLOYMENT COMMANDS:
""")

# Generate container deployment commands
specialists = ['mean_reversion', 'trend', 'volatility', 'breakout']

for spec in specialists:
    print(f"""
   # Deploy {spec} specialist in container:
   podman run -d \\
     --name cherokee-{spec}-specialist \\
     --network cherokee-net \\
     -e DB_HOST=192.168.132.222 \\
     -e API_ENDPOINT=http://cherokee-unified-api:4000 \\
     -e COUNCIL_ENDPOINT=http://cherokee-elder-council:4100 \\
     -v /home/dereadi/scripts/claude:/app \\
     python:3.12-slim \\
     python /app/{spec}_specialist_v2.py
   """)

print("\n5. MONITORING:")
print("   - Use podman logs for each container")
print("   - Store metrics in cherokee-postgres")
print("   - Dashboard at http://localhost:8085 (NocoBase)")

print("\n✅ TO IMPLEMENT:")
print("1. Stop all non-containerized trading")
print("2. Create Dockerfiles for specialists")
print("3. Deploy in Cherokee container network")
print("4. Use Elder Council for consensus")
print("5. Monitor via NocoBase dashboard")