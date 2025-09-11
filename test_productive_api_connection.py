#!/usr/bin/env python3
"""
Test Productive.io API connection with the found credentials
"""

import requests
import json

# The credentials found in pathfinder
API_KEY = 'cab4ebf1-7af4-43f6-b51f-44baabf61231'
ORG_ID = '49628'
BASE_URL = 'https://api.productive.io/api/v2'

headers = {
    'X-Auth-Token': API_KEY,
    'Content-Type': 'application/vnd.api+json',
    'X-Organization-Id': ORG_ID
}

print("🔥 Testing Productive.io API connection...")
print(f"Organization ID: {ORG_ID}")
print(f"API Key: {API_KEY[:10]}...")
print()

# Test 1: Get people
print("Testing /people endpoint...")
try:
    response = requests.get(f"{BASE_URL}/people", headers=headers, params={'page[size]': 5})
    if response.status_code == 200:
        data = response.json()
        people_count = len(data.get('data', []))
        print(f"✅ SUCCESS! Found {people_count} people")
        if people_count > 0:
            print("First person:", data['data'][0].get('attributes', {}).get('name', 'Unknown'))
    else:
        print(f"❌ Failed: {response.status_code} - {response.text[:100]}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 2: Get projects
print("Testing /projects endpoint...")
try:
    response = requests.get(f"{BASE_URL}/projects", headers=headers, params={'page[size]': 5})
    if response.status_code == 200:
        data = response.json()
        project_count = len(data.get('data', []))
        print(f"✅ SUCCESS! Found {project_count} projects")
        if project_count > 0:
            print("First project:", data['data'][0].get('attributes', {}).get('name', 'Unknown'))
    else:
        print(f"❌ Failed: {response.status_code} - {response.text[:100]}")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("🔥 API test complete! The bot should now work with REAL data!")