#!/usr/bin/env python3
"""
Network Comparison Tool
=======================
Compare why one node can auth but this one can't
"""

import requests
import socket
import subprocess
import json
from datetime import datetime

def compare_network():
    """Compare network characteristics"""
    
    print("🔍 NETWORK COMPARISON DIAGNOSTIC")
    print("="*60)
    
    # 1. Check our external IP (what Robinhood sees)
    print("\n1️⃣ EXTERNAL IP CHECK:")
    try:
        # Multiple services to check external IP
        ip_services = [
            'https://api.ipify.org?format=json',
            'https://ifconfig.me/all.json',
            'https://ipinfo.io/json'
        ]
        
        for service in ip_services:
            try:
                response = requests.get(service, timeout=5)
                data = response.json()
                print(f"  ✅ {service.split('/')[2]}: {data.get('ip', data)}")
                break
            except:
                continue
                
    except Exception as e:
        print(f"  ❌ Could not determine external IP: {e}")
    
    # 2. Check geolocation (some services block by country)
    print("\n2️⃣ GEOLOCATION CHECK:")
    try:
        response = requests.get('https://ipinfo.io/json', timeout=5)
        geo = response.json()
        print(f"  📍 Location: {geo.get('city', 'unknown')}, {geo.get('region', 'unknown')}, {geo.get('country', 'unknown')}")
        print(f"  🏢 ISP: {geo.get('org', 'unknown')}")
        
        # Check if we're on a known VPN/proxy/datacenter
        if 'hostname' in geo:
            hostname = geo['hostname'].lower()
            if any(x in hostname for x in ['vpn', 'proxy', 'datacenter', 'hosting', 'cloud']):
                print("  ⚠️ WARNING: Detected datacenter/VPN IP - may be blocked!")
    except:
        print("  ❌ Could not determine geolocation")
    
    # 3. Check TLS fingerprint (different TLS clients have different fingerprints)
    print("\n3️⃣ TLS FINGERPRINT CHECK:")
    try:
        # Check JA3 fingerprint
        result = subprocess.run(
            ['curl', '-s', 'https://tls.browserleaks.com/json'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            tls_data = json.loads(result.stdout)
            print(f"  🔐 JA3 Hash: {tls_data.get('ja3_hash', 'unknown')[:40]}...")
            print(f"  🌐 User Agent: {tls_data.get('user_agent', 'unknown')[:50]}...")
        else:
            print("  ⚠️ Could not determine TLS fingerprint")
    except Exception as e:
        print(f"  ❌ TLS check failed: {e}")
    
    # 4. Check if we're being rate limited
    print("\n4️⃣ RATE LIMIT CHECK:")
    endpoints = [
        'https://api.robinhood.com/',
        'https://api.robinhood.com/pathfinder/user_machine/'
    ]
    
    for endpoint in endpoints:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            }
            response = requests.get(endpoint, headers=headers, timeout=5)
            
            # Check for rate limit headers
            rate_headers = {
                'X-RateLimit-Limit': response.headers.get('X-RateLimit-Limit'),
                'X-RateLimit-Remaining': response.headers.get('X-RateLimit-Remaining'),
                'Retry-After': response.headers.get('Retry-After'),
                'CF-RAY': response.headers.get('CF-RAY')
            }
            
            print(f"\n  Endpoint: {endpoint.split('/')[-2] or 'root'}")
            print(f"    Status: {response.status_code}")
            
            for header, value in rate_headers.items():
                if value:
                    print(f"    {header}: {value}")
                    
        except requests.Timeout:
            print(f"  ⏱️ {endpoint}: TIMEOUT (possibly blocked)")
        except Exception as e:
            print(f"  ❌ {endpoint}: {str(e)[:50]}")
    
    # 5. DNS resolution comparison
    print("\n5️⃣ DNS RESOLUTION CHECK:")
    try:
        import dns.resolver
        resolver = dns.resolver.Resolver()
        
        # Try different DNS servers
        dns_servers = {
            'System': None,
            'Google': ['8.8.8.8', '8.8.4.4'],
            'Cloudflare': ['1.1.1.1', '1.0.0.1']
        }
        
        for name, servers in dns_servers.items():
            if servers:
                resolver.nameservers = servers
            
            try:
                answers = resolver.resolve('api.robinhood.com', 'A')
                ips = [str(ip) for ip in answers]
                print(f"  {name} DNS: {', '.join(ips[:3])}")
            except:
                print(f"  {name} DNS: Failed")
                
    except ImportError:
        # Fallback if dnspython not installed
        try:
            result = socket.gethostbyname('api.robinhood.com')
            print(f"  System DNS: {result}")
        except:
            print("  ❌ DNS resolution failed")
    
    # 6. Working node comparison
    print("\n6️⃣ IF ANOTHER NODE WORKS:")
    print("  Run this script on the WORKING node and compare:")
    print("  - Different external IP? (residential vs datacenter)")
    print("  - Different geolocation? (US vs international)")
    print("  - Different ISP? (consumer vs hosting provider)")
    print("  - Different TLS fingerprint? (browser vs python)")
    
    print("\n" + "="*60)
    print("💡 SOLUTIONS:")
    print("  1. Use residential proxy/VPN if on datacenter IP")
    print("  2. Use US-based connection if international")
    print("  3. Mimic browser TLS fingerprint with curl-impersonate")
    print("  4. Use working node as proxy for this one")
    print("  5. Deploy trading bot directly on working node")
    print("="*60)

if __name__ == "__main__":
    compare_network()