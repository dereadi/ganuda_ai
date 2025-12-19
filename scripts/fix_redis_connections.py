#!/usr/bin/env python3
"""
Fix Redis connection leaks in SAG files
Replaces direct redis.Redis() calls with shared pool client
"""
import os
import re

SAG_DIR = '/ganuda/home/dereadi/sag_unified_interface'

# Files to fix and their specific changes
FIXES = {
    'action_integrations.py': {
        'add_import': 'import sys; sys.path.insert(0, "/ganuda/lib"); from redis_client import get_redis',
        'remove_import': 'import redis',
        'replacements': [
            ('r = redis.Redis(**REDIS_CONFIG, decode_responses=True)', 'r = get_redis()')
        ]
    },
    'event_manager.py': {
        'add_import': 'import sys; sys.path.insert(0, "/ganuda/lib"); from redis_client import get_redis',
        'remove_import': 'import redis',
        'replacements': [
            # Replace the __init__ redis connection block
        ],
        'block_replace': {
            'start': 'self.redis_client = redis.Redis(',
            'end': 'decode_responses=True',
            'replacement': 'self.redis_client = get_redis()'
        }
    },
    'messaging.py': {
        'add_import': 'import sys; sys.path.insert(0, "/ganuda/lib"); from redis_client import get_redis',
        'remove_import': 'import redis',
        'replacements': [
            ('redis_client = redis.Redis(host=\'localhost\', port=6379, decode_responses=True)', 'redis_client = get_redis()')
        ]
    },
    'redis_subscriber.py': {
        'add_import': 'import sys; sys.path.insert(0, "/ganuda/lib"); from redis_client import get_redis, pool',
        'remove_import': 'import redis',
        'note': 'This file uses pub/sub which needs special handling - manual review needed'
    }
}

def fix_file(filename, fixes):
    filepath = os.path.join(SAG_DIR, filename)
    
    if not os.path.exists(filepath):
        print(f'  SKIP: {filename} not found')
        return False
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Remove old import
    if 'remove_import' in fixes:
        content = content.replace(fixes['remove_import'] + '\n', '')
    
    # Add new import after other imports
    if 'add_import' in fixes:
        # Find last import line
        lines = content.split('\n')
        last_import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                last_import_idx = i
        
        # Insert new import
        lines.insert(last_import_idx + 1, fixes['add_import'])
        content = '\n'.join(lines)
    
    # Simple replacements
    if 'replacements' in fixes:
        for old, new in fixes['replacements']:
            content = content.replace(old, new)
    
    if content != original:
        # Backup
        backup_path = filepath + '.bak'
        with open(backup_path, 'w') as f:
            f.write(original)
        
        # Write fixed version
        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f'  FIXED: {filename} (backup at {backup_path})')
        return True
    else:
        print(f'  UNCHANGED: {filename}')
        return False

if __name__ == '__main__':
    print('Fixing Redis connections in SAG files...')
    print()
    
    for filename, fixes in FIXES.items():
        print(f'Processing {filename}:')
        if 'note' in fixes:
            print(f'  NOTE: {fixes["note"]}')
        fix_file(filename, fixes)
    
    print()
    print('Done. Please restart SAG to apply changes.')
    print('  systemctl restart sag  # or kill and restart app.py')
