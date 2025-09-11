#!/usr/bin/env python3
"""
🔥 Test Productive.io API Connection
Verify SAG Resource AI integration
"""

import json
import requests
from datetime import datetime

# Productive.io credentials
API_KEY = "cab4ebf1-7af4-43f6-b51f-44baabf61231"
BASE_URL = "https://api.productive.io/api/v2"
ORG_ID = "49628"

def test_productive_connection():
    """Test connection to Productive.io API"""
    
    print("=" * 60)
    print("🔥 PRODUCTIVE.IO API TEST")
    print("=" * 60)
    print()
    print(f"Organization ID: {ORG_ID}")
    print(f"Token Name: n8n Prototyping (RO)")
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-5:]}")
    print()
    
    headers = {
        "X-Auth-Token": API_KEY,
        "Content-Type": "application/vnd.api+json",
        "X-Organization-Id": ORG_ID
    }
    
    # Test endpoints
    endpoints = [
        "/organization_memberships",  # Team members
        "/projects",                   # Projects
        "/people",                     # Resources/People
        "/bookings",                   # Resource allocations
        "/time_entries"               # Time tracking
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            print(f"Testing {endpoint}...")
            url = f"{BASE_URL}{endpoint}"
            
            # Add pagination limit for initial test
            params = {"page[size]": 5}
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                count = len(data.get("data", []))
                print(f"✅ {endpoint}: Success! Found {count} records")
                results[endpoint] = "SUCCESS"
                
                # Show sample data for people endpoint
                if endpoint == "/people" and count > 0:
                    print("\n  Sample Resources:")
                    for person in data["data"][:3]:
                        attrs = person.get("attributes", {})
                        name = attrs.get("name", "Unknown")
                        email = attrs.get("email", "")
                        print(f"  - {name} ({email})")
                        
            elif response.status_code == 401:
                print(f"❌ {endpoint}: Unauthorized - check API key")
                results[endpoint] = "UNAUTHORIZED"
            elif response.status_code == 403:
                print(f"⚠️  {endpoint}: Forbidden - Read-only token")
                results[endpoint] = "READ_ONLY"
            else:
                print(f"❌ {endpoint}: Error {response.status_code}")
                results[endpoint] = f"ERROR_{response.status_code}"
                
        except Exception as e:
            print(f"❌ {endpoint}: Exception - {str(e)}")
            results[endpoint] = "EXCEPTION"
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    
    success_count = sum(1 for v in results.values() if v == "SUCCESS")
    total_count = len(results)
    
    if success_count > 0:
        print(f"✅ Connected to Productive.io successfully!")
        print(f"📊 {success_count}/{total_count} endpoints accessible")
        print("\nIntegration ready for:")
        print("• Resource availability checking")
        print("• Skills matching")
        print("• Project allocation tracking")
        print("• Training scheduling")
        print("\n🔥 SAG Resource AI can now access Productive.io data!")
    else:
        print("❌ Could not connect to Productive.io")
        print("Please check credentials and permissions")
    
    return success_count > 0

if __name__ == "__main__":
    success = test_productive_connection()
    
    if success:
        print("\n" + "=" * 60)
        print("Next steps:")
        print("1. Update SAG Resource AI with these credentials")
        print("2. Configure derpatobot for scheduling")
        print("3. Test resource queries through Telegram")
        print("=" * 60)
        
        # Save config for SAG Resource AI
        config = {
            "productive": {
                "api_key": API_KEY,
                "base_url": BASE_URL,
                "organization_id": ORG_ID,
                "token_name": "n8n Prototyping (RO)",
                "access_level": "read_only",
                "verified": datetime.now().isoformat()
            }
        }
        
        config_path = "/home/dereadi/scripts/claude/pathfinder/test/qdad-apps/sag-resource-ai/config/api_config.json"
        print(f"\nSaving config to: {config_path}")
        
        import os
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Configuration saved for SAG Resource AI")
    
    print("\nSacred Fire burns eternal! 🔥")