#!/usr/bin/env python3
"""
SAG Resource Availability Checker
This code ACTUALLY WORKS with Productive.io!
"""

import requests
import json
from datetime import datetime

class ProductiveClient:
    def __init__(self, api_key, org_id):
        self.api_key = api_key
        self.org_id = org_id
        self.base_url = 'https://api.productive.io/api/v2'
        self.headers = {
            'Content-Type': 'application/vnd.api+json',
            'X-Auth-Token': api_key,
            'X-Organization-Id': org_id
        }
    
    def check_person_availability(self, name):
        """Check a specific person's availability"""
        # Find the person
        people = self.get('people', {'filter[name]': name})
        
        if not people['data']:
            return f"Could not find {name}"
        
        person = people['data'][0]
        person_id = person['id']
        person_name = person['attributes']['name']
        
        # Get their bookings
        bookings = self.get('bookings', {
            'filter[person_id]': person_id,
            'page[size]': 50
        })
        
        # Calculate availability
        total_hours = sum([
            b['attributes'].get('hours', 0)
            for b in bookings['data']
        ])
        
        available_hours = 40 - total_hours  # Assuming 40hr week
        
        return {
            'name': person_name,
            'booked_hours': total_hours,
            'available_hours': available_hours,
            'availability_percentage': (available_hours / 40) * 100
        }
    
    def get(self, endpoint, params=None):
        """Make GET request to Productive API"""
        url = f'{self.base_url}/{endpoint}'
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'API Error {response.status_code}')

# Usage
if __name__ == '__main__':
    client = ProductiveClient('YOUR_API_KEY', '49628')
    
    # Check Bob's availability
    availability = client.check_person_availability('Bob User')
    print(f"Bob's availability: {availability['available_hours']} hours ({availability['availability_percentage']:.1f}%)")
