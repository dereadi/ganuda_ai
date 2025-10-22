#!/bin/bash
set -e

echo "🔥 EXECUTIVE JR - DEPLOYING THERMAL MEMORY DATABASE ON BLUEFIN"
echo "================================================================"

# 1. Stop any existing PostgreSQL containers
echo ""
echo "🧹 Cleaning up any existing containers..."
ssh bluefin "docker stop bluefin-thermal-db 2>/dev/null || echo '   No existing container to stop'"
ssh bluefin "docker rm bluefin-thermal-db 2>/dev/null || echo '   No existing container to remove'"

# 2. Start PostgreSQL container
echo ""
echo "🚀 Starting PostgreSQL container..."
ssh bluefin "docker run -d \
    --name bluefin-thermal-db \
    -e POSTGRES_DB=sag_thermal_memory \
    -e POSTGRES_USER=claude \
    -e POSTGRES_PASSWORD=jawaseatlasers2 \
    -p 5433:5432 \
    -v /home/dereadi/scripts/sag-spoke/thermal_db:/var/lib/postgresql/data \
    postgres:15"

# 3. Wait for database to be ready
echo ""
echo "⏳ Waiting for database to start (15 seconds)..."
sleep 15

# 4. Verify database is running
echo ""
echo "🔍 Verifying database status..."
ssh bluefin "docker ps | grep bluefin-thermal-db" && echo "   ✅ Container running" || echo "   ❌ Container not found"

# 5. Create thermal_memory_archive schema
echo ""
echo "🏗️  Creating thermal_memory_archive table..."
ssh bluefin "PGPASSWORD=jawaseatlasers2 psql \
    -h localhost \
    -p 5433 \
    -U claude \
    -d sag_thermal_memory \
    -c \"
    CREATE TABLE IF NOT EXISTS thermal_memory_archive (
        id SERIAL PRIMARY KEY,
        content_summary TEXT,
        temperature_score FLOAT,
        access_count INTEGER DEFAULT 1,
        phase_coherence FLOAT DEFAULT 0.5,
        sacred_pattern BOOLEAN DEFAULT false,
        created_at TIMESTAMP DEFAULT NOW(),
        last_access TIMESTAMP DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_temperature ON thermal_memory_archive(temperature_score);
    CREATE INDEX IF NOT EXISTS idx_sacred ON thermal_memory_archive(sacred_pattern);
    CREATE INDEX IF NOT EXISTS idx_created ON thermal_memory_archive(created_at);
    \""

# 6. Verify table creation
echo ""
echo "✅ Verifying table structure..."
ssh bluefin "PGPASSWORD=jawaseatlasers2 psql \
    -h localhost -p 5433 -U claude -d sag_thermal_memory \
    -c '\\d thermal_memory_archive'" | head -20

echo ""
echo "🎯 THERMAL MEMORY DATABASE DEPLOYMENT COMPLETE"
echo "================================================================"
echo "   Host: bluefin"
echo "   Port: 5433"
echo "   Database: sag_thermal_memory"
echo "   Table: thermal_memory_archive"
echo "   Status: READY FOR DATA"
