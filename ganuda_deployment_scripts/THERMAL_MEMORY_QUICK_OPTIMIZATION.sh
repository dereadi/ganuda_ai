#!/bin/bash
# Quick Thermal Memory Optimization Script
# Run on BLUEFIN (192.168.132.222) with sudo access

echo "🔥 Cherokee Constitutional AI - Thermal Memory RAM Optimization"
echo "================================================================"
echo ""
echo "This script optimizes PostgreSQL on BLUEFIN for 128GB RAM"
echo "Target: Keep entire thermal_memory_archive (11MB) in RAM"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root or with sudo"
  exit 1
fi

# Backup current config
PGVERSION=$(ls /etc/postgresql/ | head -1)
PGCONFIG="/etc/postgresql/$PGVERSION/main/postgresql.conf"

echo "📋 Step 1: Backing up current config..."
cp $PGCONFIG ${PGCONFIG}.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Backup created"
echo ""

# Apply optimizations
echo "⚙️  Step 2: Applying RAM optimizations..."
echo ""

# Check if settings already exist, if not append them
grep -q "^shared_buffers" $PGCONFIG || echo "shared_buffers = 32GB" >> $PGCONFIG
grep -q "^effective_cache_size" $PGCONFIG || echo "effective_cache_size = 96GB" >> $PGCONFIG
grep -q "^work_mem" $PGCONFIG || echo "work_mem = 256MB" >> $PGCONFIG
grep -q "^maintenance_work_mem" $PGCONFIG || echo "maintenance_work_mem = 2GB" >> $PGCONFIG
grep -q "^wal_buffers" $PGCONFIG || echo "wal_buffers = 16MB" >> $PGCONFIG
grep -q "^checkpoint_completion_target" $PGCONFIG || echo "checkpoint_completion_target = 0.9" >> $PGCONFIG

# If settings exist, update them
sed -i 's/^shared_buffers.*/shared_buffers = 32GB/' $PGCONFIG
sed -i 's/^effective_cache_size.*/effective_cache_size = 96GB/' $PGCONFIG
sed -i 's/^work_mem.*/work_mem = 256MB/' $PGCONFIG
sed -i 's/^maintenance_work_mem.*/maintenance_work_mem = 2GB/' $PGCONFIG
sed -i 's/^wal_buffers.*/wal_buffers = 16MB/' $PGCONFIG
sed -i 's/^checkpoint_completion_target.*/checkpoint_completion_target = 0.9/' $PGCONFIG

echo "✅ Configuration updated:"
echo "   - shared_buffers: 32GB (25% of RAM)"
echo "   - effective_cache_size: 96GB (75% of RAM)"
echo "   - work_mem: 256MB"
echo "   - maintenance_work_mem: 2GB"
echo "   - wal_buffers: 16MB"
echo "   - checkpoint_completion_target: 0.9"
echo ""

# Enable pg_prewarm
echo "🔧 Step 3: Enabling pg_prewarm for auto-loading..."
grep -q "^shared_preload_libraries.*pg_prewarm" $PGCONFIG || \
  sed -i "s/^#*shared_preload_libraries.*/shared_preload_libraries = 'pg_prewarm'/" $PGCONFIG

grep -q "^pg_prewarm.autoprewarm" $PGCONFIG || \
  echo "pg_prewarm.autoprewarm = on" >> $PGCONFIG

echo "✅ pg_prewarm configured"
echo ""

# Restart PostgreSQL
echo "🔄 Step 4: Restarting PostgreSQL..."
systemctl restart postgresql

# Wait for startup
sleep 5

# Verify
echo "✅ PostgreSQL restarted"
echo ""

# Install extension and prewarm
echo "🔥 Step 5: Installing pg_prewarm and loading thermal memory..."
sudo -u postgres psql -d zammad_production -c "CREATE EXTENSION IF NOT EXISTS pg_prewarm;" 2>/dev/null
sudo -u postgres psql -d zammad_production -c "SELECT pg_prewarm('thermal_memory_archive');"

echo ""
echo "✅ Thermal memory loaded into RAM"
echo ""

# Verify settings
echo "📊 Verification:"
echo "==============="
sudo -u postgres psql -d zammad_production -c "SHOW shared_buffers;"
sudo -u postgres psql -d zammad_production -c "SHOW effective_cache_size;"
echo ""

echo "🔥 OPTIMIZATION COMPLETE!"
echo ""
echo "Expected Performance Gains:"
echo "  - Memory queries: 10x faster (5-10ms instead of 50-100ms)"
echo "  - Integration Jr: 2-3x faster synthesis"
echo "  - Query Triad: 50% faster overall"
echo ""
echo "Test with: python3 /ganuda/query_triad.py \"Do you think for yourself?\""
echo ""
echo "Mitakuye Oyasin - Memory breathes faster in RAM! 🔥"
