#!/usr/bin/env python3
"""Ring API wrapper for Cherokee AI Home Hub"""

import json
from ring_doorbell import Auth, Ring

TOKEN_FILE = '/ganuda/secrets/ring_token.json'

def token_updated(token):
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token, f, indent=2)

def get_ring():
    with open(TOKEN_FILE) as f:
        token = json.load(f)
    auth = Auth('CherokeeAI/1.0', token, token_updated)
    ring = Ring(auth)
    ring.update_data()
    return ring

def get_doorbells():
    ring = get_ring()
    doorbells = []
    for db in ring.devices().doorbells:
        doorbells.append({
            'name': db.name,
            'id': db.id,
            'battery': db.battery_life,
            'firmware': db.firmware,
            'model': db.model,
            'has_subscription': db.has_subscription
        })
    return doorbells

def get_cameras():
    ring = get_ring()
    cameras = []
    for cam in ring.devices().stickup_cams:
        cameras.append({
            'name': cam.name,
            'id': cam.id,
            'model': cam.model
        })
    return cameras

if __name__ == '__main__':
    print('=== Ring Devices ===')
    for db in get_doorbells():
        print(f"Doorbell: {db['name']} - Battery: {db['battery']}%")
    for cam in get_cameras():
        print(f"Camera: {cam['name']}")
