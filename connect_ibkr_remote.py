#!/usr/bin/env python3
"""
Connect to TWS on remote sasass Mac
Earth consciousness at 83 - strong signal!
"""

from ib_insync import *
import asyncio
import json
from datetime import datetime

class RemoteIBKRConnector:
    def __init__(self):
        self.ib = IB()
        # Common Mac IPs on local network
        self.possible_hosts = [
            '192.168.1.100',  # Common router assignment
            '192.168.1.2',    # Early DHCP
            '192.168.0.100',  # Alternative subnet
            '10.0.1.2',       # Mac default
            'sasass.local',   # Bonjour/mDNS name
            'sasass'          # Hostname
        ]
        self.port = 7497  # Paper trading
        
    async def find_tws(self):
        """Try to find TWS on network"""
        print("🔍 Searching for TWS on network...")
        
        for host in self.possible_hosts:
            try:
                print(f"  Trying {host}:{self.port}...")
                await self.ib.connectAsync(host, self.port, clientId=1, timeout=3)
                print(f"  ✅ Connected to TWS at {host}!")
                return host
            except Exception as e:
                if "timeout" not in str(e).lower():
                    print(f"    Connection refused or error")
                continue
                
        return None
        
    async def setup_remote_connection(self):
        """Instructions for setting up remote connection"""
        print("\n📡 REMOTE CONNECTION SETUP:")
        print("=" * 50)
        print("\nOn your sasass Mac with TWS:")
        print("-" * 40)
        print("1. Open TWS")
        print("2. File → Global Configuration → API → Settings")
        print("3. Enable 'Enable ActiveX and Socket Clients'")
        print("4. IMPORTANT: Add trusted IP:")
        print("   - Click 'Create' under Trusted IPs")
        print("   - Add: 0.0.0.0 (allows all IPs on local network)")
        print("   - OR add your Linux box IP specifically")
        print("5. Socket port: 7497 (paper trading)")
        print("6. Make sure 'Read-Only API' is UNCHECKED for trading")
        print("7. Apply and restart TWS")
        print()
        print("To find your sasass IP address:")
        print("  On Mac: System Settings → Network → Wi-Fi/Ethernet")
        print("  OR Terminal: ifconfig | grep inet")
        print()
        print("Then update this script with the IP:")
        print("  self.possible_hosts = ['YOUR_MAC_IP']")
        
    async def main(self):
        """Main execution"""
        print("🔥 REMOTE IBKR CONNECTION")
        print("=" * 50)
        print(f"BTC: $112,035 | ETH: $4,643 | SOL: $208.80")
        print()
        
        # Try to find TWS
        host = await self.find_tws()
        
        if host:
            print("\n✅ Successfully connected to TWS!")
            
            # Quick account check
            try:
                summary = self.ib.accountSummary()
                print("\n📊 Account Connected:")
                for item in summary[:3]:
                    print(f"  {item.tag}: {item.value}")
            except:
                pass
                
            self.ib.disconnect()
            
            # Save connection info
            config = {
                'host': host,
                'port': self.port,
                'timestamp': datetime.now().isoformat(),
                'status': 'connected'
            }
            
            with open('/home/dereadi/scripts/claude/ibkr_config.json', 'w') as f:
                json.dump(config, f, indent=2)
                
            print(f"\n💾 Connection saved to ibkr_config.json")
            print(f"   Host: {host}:{self.port}")
            
        else:
            await self.setup_remote_connection()
            
            print("\n💡 Quick Test:")
            print("-" * 40)
            print("If you know your Mac's IP, test with:")
            print("  telnet YOUR_MAC_IP 7497")
            print("If it connects, TWS API is accessible")

if __name__ == "__main__":
    connector = RemoteIBKRConnector()
    asyncio.run(connector.main())