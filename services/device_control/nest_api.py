#!/usr/bin/env python3
"""
Nest API wrapper for Cherokee AI Home Hub
"""

import json
import requests
from typing import Dict, List, Optional

CREDENTIALS_FILE = '/ganuda/secrets/nest_credentials.json'
TOKENS_FILE = '/ganuda/secrets/nest_tokens.json'

def load_config():
    with open(CREDENTIALS_FILE) as f:
        creds = json.load(f)
    with open(TOKENS_FILE) as f:
        tokens = json.load(f)
    return creds, tokens

def refresh_token():
    """Refresh the access token using refresh_token."""
    creds, tokens = load_config()
    
    resp = requests.post('https://www.googleapis.com/oauth2/v4/token', data={
        'client_id': creds['client_id'],
        'client_secret': creds['client_secret'],
        'refresh_token': tokens['refresh_token'],
        'grant_type': 'refresh_token'
    })
    
    if resp.status_code == 200:
        new_tokens = resp.json()
        new_tokens['refresh_token'] = tokens['refresh_token']
        with open(TOKENS_FILE, 'w') as f:
            json.dump(new_tokens, f, indent=2)
        return new_tokens['access_token']
    return None

def get_devices() -> List[Dict]:
    """Get all Nest devices."""
    creds, tokens = load_config()
    project_id = creds['project_id']
    
    headers = {'Authorization': f'Bearer {tokens["access_token"]}'}
    url = f'https://smartdevicemanagement.googleapis.com/v1/enterprises/{project_id}/devices'
    
    resp = requests.get(url, headers=headers)
    
    if resp.status_code == 401:
        # Token expired, refresh and retry
        new_token = refresh_token()
        if new_token:
            headers = {'Authorization': f'Bearer {new_token}'}
            resp = requests.get(url, headers=headers)
    
    if resp.status_code == 200:
        return resp.json().get('devices', [])
    return []

def get_thermostat_status() -> Optional[Dict]:
    """Get thermostat status."""
    devices = get_devices()
    
    for device in devices:
        if 'THERMOSTAT' in device.get('type', ''):
            traits = device.get('traits', {})
            
            # Temperature
            temp_trait = traits.get('sdm.devices.traits.Temperature', {})
            current_temp_c = temp_trait.get('ambientTemperatureCelsius', 0)
            current_temp_f = current_temp_c * 9/5 + 32
            
            # Humidity
            humidity_trait = traits.get('sdm.devices.traits.Humidity', {})
            humidity = humidity_trait.get('ambientHumidityPercent', 0)
            
            # Thermostat mode
            mode_trait = traits.get('sdm.devices.traits.ThermostatMode', {})
            mode = mode_trait.get('mode', 'OFF')
            
            # Target temperature
            setpoint_trait = traits.get('sdm.devices.traits.ThermostatTemperatureSetpoint', {})
            if mode == 'HEAT':
                target_c = setpoint_trait.get('heatCelsius', 0)
            elif mode == 'COOL':
                target_c = setpoint_trait.get('coolCelsius', 0)
            else:
                target_c = 0
            target_f = target_c * 9/5 + 32 if target_c else 0
            
            # HVAC status
            hvac_trait = traits.get('sdm.devices.traits.ThermostatHvac', {})
            hvac_status = hvac_trait.get('status', 'OFF')
            
            return {
                'device_id': device['name'].split('/')[-1],
                'device_name': device['name'],
                'current_temp_f': round(current_temp_f, 1),
                'current_temp_c': round(current_temp_c, 1),
                'target_temp_f': round(target_f, 1),
                'humidity': humidity,
                'mode': mode,
                'hvac_status': hvac_status
            }
    return None

def set_thermostat_temp(device_name: str, temp_f: float, mode: str = None) -> Dict:
    """Set thermostat temperature."""
    creds, tokens = load_config()
    
    temp_c = (temp_f - 32) * 5/9
    
    # Determine command based on mode
    if mode == 'HEAT' or mode is None:
        command = 'sdm.devices.commands.ThermostatTemperatureSetpoint.SetHeat'
        params = {'heatCelsius': temp_c}
    elif mode == 'COOL':
        command = 'sdm.devices.commands.ThermostatTemperatureSetpoint.SetCool'
        params = {'coolCelsius': temp_c}
    else:
        return {'error': f'Unknown mode: {mode}'}
    
    headers = {
        'Authorization': f'Bearer {tokens["access_token"]}',
        'Content-Type': 'application/json'
    }
    url = f'https://smartdevicemanagement.googleapis.com/v1/{device_name}:executeCommand'
    
    resp = requests.post(url, headers=headers, json={
        'command': command,
        'params': params
    })
    
    if resp.status_code == 200:
        return {'status': 'ok', 'target_temp_f': temp_f}
    return {'error': resp.text}

def set_thermostat_mode(device_name: str, mode: str) -> Dict:
    """Set thermostat mode (HEAT, COOL, HEATCOOL, OFF)."""
    creds, tokens = load_config()
    
    headers = {
        'Authorization': f'Bearer {tokens["access_token"]}',
        'Content-Type': 'application/json'
    }
    url = f'https://smartdevicemanagement.googleapis.com/v1/{device_name}:executeCommand'
    
    resp = requests.post(url, headers=headers, json={
        'command': 'sdm.devices.commands.ThermostatMode.SetMode',
        'params': {'mode': mode.upper()}
    })
    
    if resp.status_code == 200:
        return {'status': 'ok', 'mode': mode}
    return {'error': resp.text}

def get_cameras() -> List[Dict]:
    """Get camera info (snapshots require additional setup)."""
    devices = get_devices()
    cameras = []
    
    for device in devices:
        if 'CAMERA' in device.get('type', ''):
            traits = device.get('traits', {})
            info = traits.get('sdm.devices.traits.Info', {})
            
            cameras.append({
                'device_id': device['name'].split('/')[-1],
                'device_name': device['name'],
                'custom_name': info.get('customName', 'Nest Camera'),
                'type': 'CAMERA'
            })
    
    return cameras

if __name__ == '__main__':
    print('=== Nest Device Status ===')
    
    thermo = get_thermostat_status()
    if thermo:
        print(f"\nThermostat:")
        print(f"  Current: {thermo['current_temp_f']}°F")
        print(f"  Target:  {thermo['target_temp_f']}°F")
        print(f"  Mode:    {thermo['mode']}")
        print(f"  HVAC:    {thermo['hvac_status']}")
        print(f"  Humidity: {thermo['humidity']}%")
    
    cameras = get_cameras()
    print(f"\nCameras: {len(cameras)}")
    for cam in cameras:
        print(f"  - {cam['custom_name']}")
