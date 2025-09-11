#!/bin/bash
# Setup SSH tunnel to route Robinhood through residential IP

echo "🏠 RESIDENTIAL PROXY SETUP"
echo "=========================="
echo ""
echo "This will route Robinhood API calls through your home connection"
echo ""

# Option 1: SSH SOCKS Proxy (Easiest)
echo "OPTION 1: SSH SOCKS Proxy"
echo "-------------------------"
echo "From THIS server, run:"
echo "ssh -D 8080 -N user@YOUR_HOME_IP"
echo ""
echo "Then in Python, use:"
echo "export https_proxy=socks5://localhost:8080"
echo ""

# Option 2: Reverse SSH Tunnel
echo "OPTION 2: Reverse Tunnel"
echo "------------------------"
echo "From your HOME machine, run:"
echo "ssh -R 8443:api.robinhood.com:443 dereadi@192.168.132.223"
echo ""
echo "This forwards port 8443 on this server to Robinhood through your home"
echo ""

# Option 3: OpenVPN from home
echo "OPTION 3: OpenVPN Server at Home"
echo "---------------------------------"
echo "Set up OpenVPN server on your home network"
echo "Connect this server as a client"
echo ""

# Test if we're on residential
cat > test_residential.py << 'EOF'
import requests
import json

def test_ip_type():
    """Check if current IP is residential"""
    try:
        # Check IP info
        response = requests.get('https://ipinfo.io/json', timeout=5)
        data = response.json()
        
        print(f"Current IP: {data.get('ip')}")
        print(f"ISP: {data.get('org')}")
        
        # Check if residential
        org = data.get('org', '').lower()
        residential_keywords = ['comcast', 'verizon', 'att', 'spectrum', 'cox', 'charter', 'centurylink', 'frontier']
        datacenter_keywords = ['hosting', 'cloud', 'datacenter', 'amazon', 'google', 'digital ocean', 'linode']
        
        is_residential = any(keyword in org for keyword in residential_keywords)
        is_datacenter = any(keyword in org for keyword in datacenter_keywords)
        
        if is_residential:
            print("✅ Appears to be RESIDENTIAL IP - Should work with Robinhood!")
        elif is_datacenter:
            print("❌ Datacenter IP detected - Robinhood will block this")
        else:
            print("⚠️ Unknown IP type - Test with Robinhood")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ip_type()
EOF

echo ""
echo "To test if you're on residential IP:"
echo "python3 test_residential.py"
echo ""
echo "=========================="