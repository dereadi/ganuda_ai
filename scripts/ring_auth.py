#!/usr/bin/env python3
"""One-time Ring authentication script with 2FA support."""

import sys
sys.path.insert(0, '/ganuda/services/device_control/venv/lib/python3.12/site-packages')

from ring_doorbell import Auth, Ring
from ring_doorbell.exceptions import Requires2FAError
import json

def token_updated(token):
    with open('/ganuda/secrets/ring_token.json', 'w') as f:
        json.dump(token, f, indent=2)
    print('Token saved!')

def main():
    print('\n=== Ring Doorbell Authentication ===\n')
    username = input('Ring email: ').strip()
    password = input('Ring password: ').strip()

    auth = Auth('CherokeeAI/1.0', None, token_updated)

    try:
        auth.fetch_token(username, password)
    except Requires2FAError:
        print('\n2FA required. Check your phone/email for the code.')
        code = input('Enter 2FA code: ').strip()
        auth.fetch_token(username, password, code)

    # Save the token
    token_updated(auth.token)
    
    # Test the connection
    print('\nTesting connection...')
    ring = Ring(auth)
    ring.update_data()
    
    devices = ring.devices()
    doorbells = devices.get('doorbells', [])
    stickup_cams = devices.get('stickup_cams', [])
    chimes = devices.get('chimes', [])
    
    print(f'\nFound {len(doorbells)} doorbell(s), {len(stickup_cams)} camera(s), {len(chimes)} chime(s)')
    
    for db in doorbells:
        print(f'  Doorbell: {db.name} (Battery: {db.battery_life}%)')
    for cam in stickup_cams:
        print(f'  Camera: {cam.name}')
    for chime in chimes:
        print(f'  Chime: {chime.name}')
    
    print('\nRing authentication complete!')

if __name__ == '__main__':
    main()
