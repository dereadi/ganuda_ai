#!/usr/bin/env python3
"""
Debug Robinhood Authentication
===============================
Capture exactly what's being sent/received
"""

import requests
import json
from datetime import datetime
import socket
import platform

# Get system info
def get_system_info():
    """Get identifying info about this system"""
    info = {
        'hostname': socket.gethostname(),
        'ip': socket.gethostbyname(socket.gethostname()),
        'platform': platform.platform(),
        'python': platform.python_version(),
        'timestamp': datetime.now().isoformat()
    }
    return info

# Test basic connectivity
def test_connectivity():
    """Test if we can reach Robinhood"""
    endpoints = [
        'https://api.robinhood.com/',
        'https://api.robinhood.com/api-token-auth/',
        'https://nummus.robinhood.com/',
        'https://bonfire.robinhood.com/'
    ]
    
    results = {}
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=5)
            results[endpoint] = {
                'status': response.status_code,
                'headers': dict(response.headers),
                'content_length': len(response.text)
            }
        except Exception as e:
            results[endpoint] = {'error': str(e)}
    
    return results

# Test authentication endpoint
def test_auth_endpoint():
    """Test the authentication endpoint with minimal payload"""
    url = 'https://api.robinhood.com/api-token-auth/'
    
    # Different client IDs that have been used
    client_ids = [
        'c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS',  # Old one
        'c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFT',  # Variant
    ]
    
    # Different user agents
    user_agents = [
        'Robinhood/823 (iPhone; iOS 7.1.2; Scale/2.00)',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'robin_stocks/3.4.0',
        'Python/3.12'
    ]
    
    results = []
    for client_id in client_ids:
        for user_agent in user_agents:
            headers = {
                'User-Agent': user_agent,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-Robinhood-API-Version': '1.0.0'
            }
            
            payload = {
                'client_id': client_id,
                'expires_in': 86400,
                'grant_type': 'password',
                'password': 'test',
                'username': 'test',
                'scope': 'internal'
            }
            
            try:
                response = requests.post(
                    url, 
                    json=payload, 
                    headers=headers,
                    timeout=10
                )
                
                results.append({
                    'client_id': client_id[:10] + '...',
                    'user_agent': user_agent[:30],
                    'status': response.status_code,
                    'response': response.text[:200] if response.text else 'empty'
                })
            except Exception as e:
                results.append({
                    'client_id': client_id[:10] + '...',
                    'user_agent': user_agent[:30],
                    'error': str(e)
                })
    
    return results

# Check if we're being blocked
def check_blocking():
    """Check if we're being rate limited or blocked"""
    
    # Check if we can resolve DNS
    try:
        ip = socket.gethostbyname('api.robinhood.com')
        dns_ok = True
        resolved_ip = ip
    except:
        dns_ok = False
        resolved_ip = None
    
    # Check CloudFront headers
    try:
        response = requests.head('https://api.robinhood.com/', timeout=5)
        cf_ray = response.headers.get('CF-RAY', 'none')
        cf_cache = response.headers.get('x-cache', 'none')
        server = response.headers.get('server', 'none')
    except:
        cf_ray = 'error'
        cf_cache = 'error'
        server = 'error'
    
    return {
        'dns_resolves': dns_ok,
        'resolved_ip': resolved_ip,
        'cloudfront_ray': cf_ray,
        'cache_status': cf_cache,
        'server': server
    }

# Main debug function
def main():
    print("="*60)
    print("ROBINHOOD AUTHENTICATION DEBUG")
    print("="*60)
    
    # System info
    print("\n📍 SYSTEM INFO:")
    info = get_system_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # Connectivity test
    print("\n🌐 CONNECTIVITY TEST:")
    connectivity = test_connectivity()
    for endpoint, result in connectivity.items():
        if 'error' in result:
            print(f"  ❌ {endpoint}: {result['error']}")
        else:
            print(f"  ✅ {endpoint}: Status {result['status']}")
    
    # Auth endpoint test
    print("\n🔐 AUTH ENDPOINT TEST:")
    auth_results = test_auth_endpoint()
    for result in auth_results:
        if 'error' in result:
            print(f"  ❌ {result['client_id']} + {result['user_agent']}: {result['error']}")
        else:
            print(f"  📊 {result['client_id']} + {result['user_agent']}: Status {result['status']}")
            if result['status'] != 200:
                print(f"     Response: {result['response']}")
    
    # Blocking check
    print("\n🚫 BLOCKING CHECK:")
    blocking = check_blocking()
    for key, value in blocking.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*60)
    print("DIAGNOSIS:")
    
    # Analyze results
    if not blocking['dns_resolves']:
        print("❌ DNS resolution failed - network issue")
    elif 'CloudFront' in str(blocking.get('server', '')):
        print("⚠️ Traffic going through CloudFront CDN")
    
    if any('timeout' in str(r.get('error', '')).lower() for r in auth_results):
        print("❌ Authentication endpoints timing out")
        print("   Possible causes:")
        print("   - IP address blocked/rate limited")
        print("   - Geographic restrictions")
        print("   - CloudFront/WAF rules")
    
    if all(r.get('status', 0) >= 400 for r in auth_results if 'status' in r):
        print("❌ All authentication attempts rejected")
        print("   Possible causes:")
        print("   - Client ID no longer valid")
        print("   - User-Agent filtering")
        print("   - API deprecated")
    
    print("="*60)

if __name__ == "__main__":
    main()