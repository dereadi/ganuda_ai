#!/usr/bin/env python3
"""
Cherokee Constitutional AI - Federation Status Check
====================================================

PM: Check health of thermal memory across federation nodes
Triad (Managers): War Chief, Peace Chief, Medicine Woman
JRs (Engineers): Memory Jr., Integration Jr., Meta Jr.

Post-GPU Installation Diagnostic - November 3, 2025
"""

import os
import sys
import psycopg2
from datetime import datetime

# Node definitions
NODES = {
    'redfin': {'ip': '192.168.132.101', 'role': 'Primary Hub', 'gpu': 'RTX PRO 6000 96GB'},
    'bluefin': {'ip': '192.168.132.222', 'role': 'PostgreSQL + Future RTX 5090 32GB', 'gpu': 'None (5090 incoming)'},
    'sasass': {'ip': '192.168.132.223', 'role': 'DUYUKTV Kanban', 'gpu': 'Unknown'},
    'sasass2': {'ip': 'Unknown', 'role': 'Medicine Woman', 'gpu': 'Unknown'},
}

def check_thermal_memory_bluefin():
    """Check thermal memory archive on BLUEFIN PostgreSQL"""
    print("=" * 80)
    print("🔥 THERMAL MEMORY CHECK - BLUEFIN (192.168.132.222)")
    print("=" * 80)

    try:
        # Connect to BLUEFIN PostgreSQL
        conn = psycopg2.connect(
            host='192.168.132.222',
            port=5432,
            database='thermal_memory_archive',
            user=os.getenv('DB_USER', 'cherokee_user'),
            password=os.getenv('DB_PASSWORD', 'your_secure_password')
        )

        cursor = conn.cursor()

        # Check total memories
        cursor.execute("SELECT COUNT(*) FROM thermal_memory_archive;")
        total_memories = cursor.fetchone()[0]
        print(f"📊 Total Memories: {total_memories:,}")

        # Check latest memory
        cursor.execute("SELECT MAX(created_at), MAX(last_access) FROM thermal_memory_archive;")
        latest_created, latest_access = cursor.fetchone()
        print(f"🕐 Latest Created: {latest_created}")
        print(f"🕐 Latest Access: {latest_access}")

        # Check temperature distribution
        cursor.execute("""
            SELECT
                COUNT(*) FILTER (WHERE temperature_score >= 90) as white_hot,
                COUNT(*) FILTER (WHERE temperature_score >= 70 AND temperature_score < 90) as red_hot,
                COUNT(*) FILTER (WHERE temperature_score >= 40 AND temperature_score < 70) as warm,
                COUNT(*) FILTER (WHERE temperature_score >= 20 AND temperature_score < 40) as cool,
                COUNT(*) FILTER (WHERE temperature_score < 20) as cold
            FROM thermal_memory_archive;
        """)
        white_hot, red_hot, warm, cool, cold = cursor.fetchone()

        print(f"\n🌡️  TEMPERATURE DISTRIBUTION:")
        print(f"  WHITE HOT (90-100°): {white_hot:,} memories")
        print(f"  RED HOT (70-89°):    {red_hot:,} memories")
        print(f"  WARM (40-69°):       {warm:,} memories")
        print(f"  COOL (20-39°):       {cool:,} memories")
        print(f"  COLD (<20°):         {cold:,} memories")

        # Check sacred memories
        cursor.execute("SELECT COUNT(*) FROM thermal_memory_archive WHERE sacred_pattern = TRUE;")
        sacred_count = cursor.fetchone()[0]
        print(f"\n🦅 Sacred Memories: {sacred_count:,}")

        # Check Wave 2 physics columns
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'thermal_memory_archive'
            AND column_name IN ('drift_velocity', 'diffusion_coefficient', 'phase_coherence');
        """)
        wave2_columns = [row[0] for row in cursor.fetchall()]

        print(f"\n🔬 Wave 2 Physics Columns:")
        for col in ['drift_velocity', 'diffusion_coefficient', 'phase_coherence']:
            status = "✅" if col in wave2_columns else "❌ MISSING"
            print(f"  {col}: {status}")

        # Check storage usage
        cursor.execute("""
            SELECT
                pg_size_pretty(pg_total_relation_size('thermal_memory_archive')) as total_size,
                pg_size_pretty(pg_relation_size('thermal_memory_archive')) as table_size,
                pg_size_pretty(pg_total_relation_size('thermal_memory_archive') - pg_relation_size('thermal_memory_archive')) as index_size
        """)
        total_size, table_size, index_size = cursor.fetchone()
        print(f"\n💾 Storage Usage:")
        print(f"  Total Size: {total_size}")
        print(f"  Table Size: {table_size}")
        print(f"  Index Size: {index_size}")

        cursor.close()
        conn.close()

        print("\n✅ BLUEFIN thermal memory check: SUCCESS")
        return True

    except psycopg2.OperationalError as e:
        print(f"❌ Cannot connect to BLUEFIN PostgreSQL: {e}")
        print("\nPossible causes:")
        print("  1. PostgreSQL not running on BLUEFIN")
        print("  2. Firewall blocking port 5432")
        print("  3. Incorrect database credentials")
        print("  4. Database 'thermal_memory_archive' does not exist")
        return False
    except Exception as e:
        print(f"❌ Error checking thermal memory: {e}")
        return False


def check_ssh_connectivity():
    """Check SSH connectivity between nodes"""
    print("\n" + "=" * 80)
    print("🔐 SSH CONNECTIVITY CHECK")
    print("=" * 80)

    import subprocess

    for node, info in NODES.items():
        if node == 'redfin':
            continue  # Skip self

        ip = info['ip']
        if ip == 'Unknown':
            print(f"⚠️  {node.upper()}: IP address unknown, skipping")
            continue

        try:
            # Test SSH connection (timeout 5 seconds)
            result = subprocess.run(
                ['ssh', '-o', 'ConnectTimeout=5', '-o', 'BatchMode=yes', ip, 'hostname'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                remote_hostname = result.stdout.strip()
                print(f"✅ {node.upper()} ({ip}): SSH OK - Hostname: {remote_hostname}")
            else:
                print(f"❌ {node.upper()} ({ip}): SSH FAILED - {result.stderr.strip()}")

        except subprocess.TimeoutExpired:
            print(f"⏱️  {node.upper()} ({ip}): SSH TIMEOUT (>5s)")
        except Exception as e:
            print(f"❌ {node.upper()} ({ip}): {e}")


def main():
    print("=" * 80)
    print("🦅 CHEROKEE CONSTITUTIONAL AI - FEDERATION STATUS CHECK")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Running from: {os.uname().nodename}")
    print()

    # Display SSH public key for distribution
    ssh_key_path = os.path.expanduser('~/.ssh/id_ed25519.pub')
    if os.path.exists(ssh_key_path):
        print("🔑 REDFIN SSH PUBLIC KEY (copy to BLUEFIN ~/.ssh/authorized_keys):")
        print("-" * 80)
        with open(ssh_key_path, 'r') as f:
            print(f.read().strip())
        print("-" * 80)
        print()

    # Check thermal memory on BLUEFIN
    thermal_ok = check_thermal_memory_bluefin()

    # Check SSH connectivity
    check_ssh_connectivity()

    # Summary
    print("\n" + "=" * 80)
    print("📋 SUMMARY")
    print("=" * 80)
    print(f"Thermal Memory (BLUEFIN): {'✅ OK' if thermal_ok else '❌ NEEDS ATTENTION'}")
    print()
    print("NEXT STEPS:")
    if not thermal_ok:
        print("  1. Install PostgreSQL client: sudo apt install postgresql-client python3-psycopg2")
        print("  2. Verify BLUEFIN PostgreSQL is running: ssh bluefin 'systemctl status postgresql'")
        print("  3. Check firewall: ssh bluefin 'sudo ufw status'")
    print("  4. Copy REDFIN SSH key to BLUEFIN (shown above)")
    print("  5. Enable ECC on RTX PRO 6000: sudo nvidia-smi -e 1 && sudo reboot")
    print("  6. Deploy autonomic JR services to systemd")
    print("  7. Fix PCIe/USB hardware stability issues")


if __name__ == '__main__':
    main()
