#!/usr/bin/env python3
"""
Deploy SwarmSys pheromone files from database to local filesystem.
Run this on each fin node: redfin, bluefin, greenfin

Usage: python3 deploy_pheromone_files.py
"""

import psycopg2
import os
import socket

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}

def main():
    hostname = socket.gethostname()
    print(f"Deploying pheromone files on {hostname}...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, filename, destination_path, content 
        FROM file_transfer_queue 
        WHERE status = 'pending'
    """)
    
    deployed = 0
    for row in cur.fetchall():
        fid, fname, dest, content = row
        
        # Ensure directory exists
        dest_dir = os.path.dirname(dest)
        os.makedirs(dest_dir, exist_ok=True)
        
        # Write file
        with open(dest, 'w') as f:
            f.write(content)
        
        # Set permissions
        os.chmod(dest, 0o644)
        
        print(f"  Deployed: {fname} -> {dest} ({len(content)} bytes)")
        deployed += 1
    
    # Mark as deployed (for this node)
    cur.execute("""
        UPDATE file_transfer_queue 
        SET status = 'deployed', deployed_at = NOW()
        WHERE status = 'pending'
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"\nDeployed {deployed} files on {hostname}")
    print("Restart jr-executor and jr-bidding services to apply changes:")
    print("  sudo systemctl restart jr-executor jr-bidding")

if __name__ == '__main__':
    main()
