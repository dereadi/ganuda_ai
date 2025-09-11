#!/usr/bin/env python3
"""
🔥 COINBASE CDP API AUTHENTICATION FIX
======================================
Fixes the 401 Unauthorized error by properly handling CDP API keys
and JWT token generation for EC private keys
"""

import json
import os
import time
import jwt
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta
import hashlib
import secrets

class CoinbaseCDPAuth:
    """
    Handles new Coinbase Developer Platform (CDP) authentication
    Properly generates JWT tokens with EC private keys
    """
    
    def __init__(self):
        self.config_file = os.path.expanduser("~/.coinbase_config.json")
        self.api_key = None
        self.api_secret = None
        self.base_url = "https://api.coinbase.com"
        
    def load_config(self):
        """Load existing configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file) as f:
                config = json.load(f)
                self.api_key = config.get("api_key")
                self.api_secret = config.get("api_secret")
                return True
        return False
    
    def generate_jwt(self, request_method, request_path):
        """
        Generate JWT token for CDP API authentication
        Handles EC private key properly
        """
        # Extract key name (last part after final /)
        key_name = self.api_key.split('/')[-1] if self.api_key else None
        
        if not key_name or not self.api_secret:
            raise ValueError("Missing API credentials")
        
        # Current time and expiry
        now = int(time.time())
        expiry = now + 120  # 2 minutes
        
        # Create JWT payload
        payload = {
            "sub": key_name,
            "iss": "coinbase-cloud",
            "nbf": now,
            "exp": expiry,
            "aud": ["retail_rest_api_proxy"],
            "uri": f"{request_method} {self.base_url}{request_path}"
        }
        
        # Load the EC private key
        try:
            private_key = serialization.load_pem_private_key(
                self.api_secret.encode('utf-8'),
                password=None,
                backend=default_backend()
            )
            
            # Generate JWT token
            token = jwt.encode(
                payload,
                private_key,
                algorithm='ES256',
                headers={"kid": key_name}
            )
            
            return token
            
        except Exception as e:
            print(f"❌ JWT generation failed: {e}")
            return None
    
    def test_authentication(self):
        """Test the authentication with a simple API call"""
        print("\n🔥 TESTING COINBASE CDP AUTHENTICATION")
        print("=" * 50)
        
        if not self.load_config():
            print("❌ No configuration found")
            print("\nPlease set up your CDP API key:")
            print("1. Go to https://www.coinbase.com/settings/api")
            print("2. Create a NEW CDP API key (not legacy)")
            print("3. Grant these permissions:")
            print("   ✅ wallet:accounts:read")
            print("   ✅ wallet:buys:create")
            print("   ✅ wallet:sells:create")
            print("   ✅ wallet:trades:create")
            return False
        
        print(f"🔑 API Key: {self.api_key[:50]}...")
        
        # Test with accounts endpoint
        endpoint = "/api/v3/brokerage/accounts"
        jwt_token = self.generate_jwt("GET", endpoint)
        
        if not jwt_token:
            print("❌ Failed to generate JWT token")
            return False
        
        # Make the API call
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }
        
        print(f"📡 Testing: {self.base_url}{endpoint}")
        
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=headers,
                timeout=10
            )
            
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Authentication successful!")
                data = response.json()
                
                if 'accounts' in data:
                    print(f"\n💰 Found {len(data['accounts'])} accounts:")
                    for acc in data['accounts'][:5]:  # Show first 5
                        balance = acc.get('available_balance', {})
                        currency = balance.get('currency', 'N/A')
                        value = balance.get('value', '0')
                        print(f"  • {currency}: {value}")
                
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
                if response.status_code == 401:
                    print("\n⚠️  Possible issues:")
                    print("1. API key may be using legacy format")
                    print("2. Account not fully verified (need Level 2 KYC)")
                    print("3. Missing required permissions")
                    print("4. IP address not whitelisted (if required)")
                
                return False
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return False
    
    def create_working_config(self):
        """Create a working configuration for the crawdads"""
        print("\n🦀 CREATING QUANTUM CRAWDAD CONFIG")
        print("=" * 50)
        
        if self.test_authentication():
            # Save working config for crawdads
            working_config = {
                "timestamp": datetime.now().isoformat(),
                "auth_method": "CDP_JWT",
                "status": "ready",
                "api_key": self.api_key,
                "api_secret": self.api_secret,
                "capital": 300.0,
                "crawdads": {
                    "Thunder": {"capital": 42.86, "personality": "aggressive"},
                    "River": {"capital": 42.86, "personality": "patient"},
                    "Mountain": {"capital": 42.86, "personality": "steady"},
                    "Fire": {"capital": 42.86, "personality": "momentum"},
                    "Wind": {"capital": 42.86, "personality": "swift"},
                    "Earth": {"capital": 42.86, "personality": "value"},
                    "Spirit": {"capital": 42.86, "personality": "quantum"}
                }
            }
            
            with open("coinbase_cdp_config.json", "w") as f:
                json.dump(working_config, f, indent=2)
            
            print("\n✅ Configuration saved to coinbase_cdp_config.json")
            print("🦀 Crawdads ready to trade with CDP authentication!")
            
            return True
        else:
            print("\n❌ Authentication test failed")
            print("Please check your API credentials and try again")
            return False

def main():
    """Main execution"""
    auth = CoinbaseCDPAuth()
    
    # First test authentication
    if auth.test_authentication():
        print("\n🎉 SUCCESS! Authentication is working!")
        auth.create_working_config()
        
        print("\n🦀 Next steps:")
        print("1. Run: python3 deploy_300_crawdads.py")
        print("2. Watch the crawdads trade with working auth!")
    else:
        print("\n📝 To fix authentication:")
        print("1. Create new CDP API key at Coinbase")
        print("2. Update ~/.coinbase_config.json")
        print("3. Run this script again")

if __name__ == "__main__":
    main()