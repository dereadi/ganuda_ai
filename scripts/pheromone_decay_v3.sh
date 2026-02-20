#!/bin/bash
source /ganuda/config/secrets.env
# Pheromone Decay v3.0 - MSP-Aligned Decay
# Fixed: Decay based on stage + age, not temperature threshold
# For Seven Generations - Cherokee AI Federation

PGPASSWORD="$CHEROKEE_DB_PASS"
export PGPASSWORD

PSQL="/usr/bin/psql -h 192.168.132.222 -U claude -d zammad_production"

LOG="/var/log/ganuda/pheromone_decay.log"
mkdir -p /var/log/ganuda
echo "$(date): Starting pheromone decay v3 (MSP-aligned)" >> $LOG

# Stage 1: WHITE_HOT older than 7 days -> RED_HOT
echo "Stage 1: WHITE_HOT > 7 days -> RED_HOT"
$PSQL -c "
UPDATE thermal_memory_archive
SET current_stage = 'RED_HOT',
    temperature_score = GREATEST(temperature_score - 5, 85),
    last_access = NOW()
WHERE current_stage = 'WHITE_HOT'
  AND created_at < NOW() - INTERVAL '7 days';
" 2>&1 | tee -a $LOG

# Stage 2: RED_HOT older than 14 days -> HOT
echo "Stage 2: RED_HOT > 14 days -> HOT"
$PSQL -c "
UPDATE thermal_memory_archive
SET current_stage = 'HOT',
    temperature_score = GREATEST(temperature_score - 10, 70),
    last_access = NOW()
WHERE current_stage = 'RED_HOT'
  AND created_at < NOW() - INTERVAL '14 days';
" 2>&1 | tee -a $LOG

# Stage 3: HOT older than 30 days -> WARM
echo "Stage 3: HOT > 30 days -> WARM"
$PSQL -c "
UPDATE thermal_memory_archive
SET current_stage = 'WARM',
    temperature_score = GREATEST(temperature_score - 15, 50),
    last_access = NOW()
WHERE current_stage = 'HOT'
  AND created_at < NOW() - INTERVAL '30 days';
" 2>&1 | tee -a $LOG

# Stage 4: WARM older than 60 days -> COOL
echo "Stage 4: WARM > 60 days -> COOL"
$PSQL -c "
UPDATE thermal_memory_archive
SET current_stage = 'COOL',
    temperature_score = GREATEST(temperature_score - 15, 30),
    last_access = NOW()
WHERE current_stage = 'WARM'
  AND created_at < NOW() - INTERVAL '60 days';
" 2>&1 | tee -a $LOG

# Stage 5: COOL older than 90 days -> COLD
echo "Stage 5: COOL > 90 days -> COLD"
$PSQL -c "
UPDATE thermal_memory_archive
SET current_stage = 'COLD',
    temperature_score = GREATEST(temperature_score - 10, 10),
    last_access = NOW()
WHERE current_stage = 'COOL'
  AND created_at < NOW() - INTERVAL '90 days';
" 2>&1 | tee -a $LOG

# Stage 6: COLD older than 180 days -> ARCHIVE
echo "Stage 6: COLD > 180 days -> ARCHIVE"
$PSQL -c "
UPDATE thermal_memory_archive
SET current_stage = 'ARCHIVE',
    temperature_score = 0,
    last_access = NOW()
WHERE current_stage = 'COLD'
  AND created_at < NOW() - INTERVAL '180 days';
" 2>&1 | tee -a $LOG

# Also transition FRESH -> WHITE_HOT after 1 day
echo "Stage 0: FRESH > 1 day -> WHITE_HOT"
$PSQL -c "
UPDATE thermal_memory_archive
SET current_stage = 'WHITE_HOT',
    last_access = NOW()
WHERE current_stage = 'FRESH'
  AND created_at < NOW() - INTERVAL '1 day';
" 2>&1 | tee -a $LOG

echo "$(date): Pheromone decay v3 complete" >> $LOG

# Report
$PSQL -c "
SELECT current_stage, COUNT(*) as count, 
       ROUND(AVG(temperature_score)::numeric, 1) as avg_temp
FROM thermal_memory_archive
GROUP BY current_stage
ORDER BY avg_temp DESC;
"
