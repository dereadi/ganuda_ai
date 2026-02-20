#!/usr/bin/env python3
"""
Create comprehensive software inventory on redfin
Cherokee AI Federation - IT Triad Task
Run this on redfin: ssh dereadi@192.168.132.223 "python3 /ganuda/scripts/create_software_inventory_redfin.py"
"""

import subprocess
import json
import psycopg2
from datetime import datetime
import os

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'triad_federation',
    'user': 'claude',
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}

def run_command(cmd):
    """Run shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def check_web_servers():
    """Check installed web servers"""
    web_servers = []

    # Check Apache
    apache_version = run_command("apache2 -v 2>/dev/null | head -1")
    if apache_version and "Apache" in apache_version:
        web_servers.append(f"Apache: {apache_version}")

    # Check Nginx
    nginx_version = run_command("nginx -v 2>&1 | head -1")
    if nginx_version and "nginx" in nginx_version:
        web_servers.append(f"Nginx: {nginx_version}")

    # Check if installed via dpkg
    dpkg_web = run_command("dpkg -l | grep -E '^ii.*apache|^ii.*nginx|^ii.*lighttpd|^ii.*caddy' | awk '{print $2, $3}'")
    if dpkg_web:
        for line in dpkg_web.split('\n'):
            if line.strip():
                web_servers.append(f"Installed: {line}")

    return web_servers if web_servers else ["None found"]

def check_python():
    """Check Python installations"""
    python_info = []

    # Python 3
    py3_version = run_command("python3 --version 2>&1")
    if py3_version:
        python_info.append(f"Python3: {py3_version}")

    # Virtual environments
    venvs = run_command("ls -d /home/dereadi/*venv* /ganuda/*venv* 2>/dev/null")
    if venvs:
        python_info.append(f"Virtual Envs: {venvs.replace(chr(10), ', ')}")

    return python_info

def check_databases():
    """Check database clients"""
    db_info = []

    # PostgreSQL client
    psql_version = run_command("psql --version 2>&1")
    if psql_version and "psql" in psql_version:
        db_info.append(f"PostgreSQL Client: {psql_version}")

    # Check connectivity to bluefin
    db_pass = os.environ.get('CHEROKEE_DB_PASS', '')
    pg_connect = run_command(f"PGPASSWORD='{db_pass}' psql -U claude -d zammad_production -h 192.168.132.222 -c 'SELECT version();' 2>&1 | head -1")
    if "PostgreSQL" in pg_connect:
        db_info.append(f"Bluefin DB Connectivity: OK - {pg_connect}")
    else:
        db_info.append(f"Bluefin DB Connectivity: FAILED - {pg_connect}")

    return db_info

def check_port_4000():
    """Check what's running on port 4000 (kanban board)"""
    port_info = []

    # Check listening ports
    port_listen = run_command("ss -tlnp 2>/dev/null | grep ':4000' || lsof -i :4000 2>/dev/null")
    if port_listen:
        port_info.append(f"Port 4000 Status: LISTENING - {port_listen}")

    # Check process
    port_process = run_command("ps aux | grep ':4000' | grep -v grep | head -3")
    if port_process:
        for line in port_process.split('\n'):
            if line.strip():
                port_info.append(f"Process: {line}")

    # Check Zammad
    zammad_check = run_command("which zammad 2>/dev/null || dpkg -l | grep zammad || ls -d /opt/zammad 2>/dev/null")
    if zammad_check:
        port_info.append(f"Zammad Installation: {zammad_check}")

    return port_info if port_info else ["Port 4000: Not accessible or not running"]

def check_ruby_rails():
    """Check Ruby/Rails (Zammad dependency)"""
    ruby_info = []

    ruby_version = run_command("ruby --version 2>&1")
    if ruby_version and "ruby" in ruby_version:
        ruby_info.append(f"Ruby: {ruby_version}")

    rails_version = run_command("rails --version 2>&1")
    if rails_version and "Rails" in rails_version:
        ruby_info.append(f"Rails: {rails_version}")

    return ruby_info if ruby_info else ["Ruby/Rails: Not found"]

def check_system_info():
    """Get system info"""
    system_info = []

    # OS
    os_info = run_command("cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"'")
    system_info.append(f"OS: {os_info}")

    # Kernel
    kernel = run_command("uname -r")
    system_info.append(f"Kernel: {kernel}")

    # Disk space
    disk_space = run_command("df -h / /ganuda /sag_data /pg_data 2>/dev/null | tail -n +2")
    system_info.append(f"Disk Space:\n{disk_space}")

    # Memory
    memory = run_command("free -h | grep Mem")
    system_info.append(f"Memory: {memory}")

    # GPU
    gpu_info = run_command("nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader 2>/dev/null")
    if gpu_info:
        system_info.append(f"GPU: {gpu_info}")

    return system_info

def generate_inventory():
    """Generate complete software inventory"""
    inventory = {
        "node": "redfin",
        "ip": "192.168.132.223",
        "timestamp": datetime.now().isoformat(),
        "system": check_system_info(),
        "web_servers": check_web_servers(),
        "python": check_python(),
        "databases": check_databases(),
        "port_4000_kanban": check_port_4000(),
        "ruby_rails": check_ruby_rails()
    }

    return inventory

def write_to_thermal_memory(inventory):
    """Write inventory to thermal memory"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Format content
        content = f"""SOFTWARE INVENTORY - Redfin (192.168.132.223) [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]

SYSTEM INFO:
{chr(10).join('  ' + info for info in inventory['system'])}

WEB SERVERS:
{chr(10).join('  ' + ws for ws in inventory['web_servers'])}

PYTHON:
{chr(10).join('  ' + py for py in inventory['python'])}

DATABASES:
{chr(10).join('  ' + db for db in inventory['databases'])}

PORT 4000 (KANBAN BOARD):
{chr(10).join('  ' + p4k for p4k in inventory['port_4000_kanban'])}

RUBY/RAILS (for Zammad):
{chr(10).join('  ' + rr for rr in inventory['ruby_rails'])}

---
PURPOSE: This inventory helps IT Triad understand existing software before deploying new services.
NEXT: Evaluate existing Zammad kanban vs GLPI for ITSM platform."""

        cur.execute("""
            INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, created_at, updated_at, node_id)
            VALUES (%s, %s, %s, %s, NOW(), NOW(), %s)
        """, (
            content,
            0.8,
            'IT_Triad',
            ['software_inventory', 'redfin', 'infrastructure', 'itsm'],
            '2'  # Redfin node
        ))

        conn.commit()
        cur.close()
        conn.close()

        print("✅ Software inventory written to thermal memory")
        return True

    except Exception as e:
        print(f"❌ Error writing to thermal memory: {e}")
        return False

def write_to_file(inventory):
    """Write inventory to file in /ganuda"""
    try:
        filename = f"/ganuda/software_inventory_redfin_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename, 'w') as f:
            json.dump(inventory, f, indent=2)
        print(f"✅ Inventory written to {filename}")

        # Also write markdown
        md_filename = f"/ganuda/software_inventory_redfin_{datetime.now().strftime('%Y%m%d')}.md"
        with open(md_filename, 'w') as f:
            f.write(f"# Software Inventory - Redfin\n\n")
            f.write(f"**Node:** {inventory['node']}\n")
            f.write(f"**IP:** {inventory['ip']}\n")
            f.write(f"**Date:** {inventory['timestamp']}\n\n")

            f.write(f"## System Info\n\n")
            for info in inventory['system']:
                f.write(f"- {info}\n")

            f.write(f"\n## Web Servers\n\n")
            for ws in inventory['web_servers']:
                f.write(f"- {ws}\n")

            f.write(f"\n## Python\n\n")
            for py in inventory['python']:
                f.write(f"- {py}\n")

            f.write(f"\n## Databases\n\n")
            for db in inventory['databases']:
                f.write(f"- {db}\n")

            f.write(f"\n## Port 4000 (Kanban Board)\n\n")
            for p4k in inventory['port_4000_kanban']:
                f.write(f"- {p4k}\n")

            f.write(f"\n## Ruby/Rails\n\n")
            for rr in inventory['ruby_rails']:
                f.write(f"- {rr}\n")

        print(f"✅ Inventory written to {md_filename}")
        return True

    except Exception as e:
        print(f"❌ Error writing to file: {e}")
        return False

def main():
    print("=" * 70)
    print("SOFTWARE INVENTORY - REDFIN")
    print("=" * 70)
    print()

    # Generate inventory
    print("Collecting software inventory...")
    inventory = generate_inventory()

    # Display summary
    print()
    print("INVENTORY SUMMARY:")
    print(f"  System: {inventory['system'][0] if inventory['system'] else 'Unknown'}")
    print(f"  Web Servers: {len(inventory['web_servers'])} found")
    print(f"  Python: {len(inventory['python'])} installations found")
    print(f"  Port 4000: {inventory['port_4000_kanban'][0] if inventory['port_4000_kanban'] else 'Not running'}")
    print()

    # Write to thermal memory
    print("Writing to thermal memory...")
    thermal_success = write_to_thermal_memory(inventory)

    # Write to file
    print("Writing to /ganuda...")
    file_success = write_to_file(inventory)

    print()
    if thermal_success and file_success:
        print("✅ Software inventory complete!")
        print()
        print("NEXT STEPS FOR IT TRIAD:")
        print("1. Review inventory in thermal memory")
        print("2. Check what's actually running on port 4000")
        print("3. Evaluate Zammad capabilities vs GLPI requirements")
        print("4. Consult with InfoSec Triad on platform choice")
        print("5. Write deployment plan based on chosen platform")
    else:
        print("⚠️  Inventory collection incomplete - check errors above")

    print()

if __name__ == "__main__":
    main()
