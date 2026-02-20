#!/bin/bash
source /ganuda/config/secrets.env
# Pheromone Decay v2.0 - More Aggressive Cooling
# Council Vote: PROCEED WITH CAUTION - Seven Generations Impact
# For Seven Generations - Cherokee AI Federation

PGPASSWORD="$CHEROKEE_DB_PASS"
export PGPASSWORD

PSQL="/usr/bin/psql -h 192.168.132.222 -U claude -d zammad_production"

LOG="/var/log/ganuda/pheromone_decay.log"
echo "$(date): Starting pheromone decay v2" >> $LOG

# Stage 1: WHITE_HOT (>95) older than 3 days -> RED_HOT (90)
$PSQL -c "
UPDATE thermal_memory_archive
SET current_stage = 'RED_HOT',
    temperature_score = 90,
    updated_at = NOW()
WHERE current_stage = 'WHITE_HOT'
  AND temperature_score > 95
  AND created_at < NOW() - INTERVAL '3 days';
" 2>&1 | tee -a $LOG

# Stage 2: RED_HOT older than 7 days -> HOT (80)
$PSQL -c "
UPDATE thermal_memory_archive
SET current_stage = 'HOT',
    temperature_score = 80,
    updated_at = NOW()
WHERE current_stage = 'RED_HOT'
  AND created_at < NOW() - INTERVAL '7 days';
" 2>&1 | tee -a $LOG

# Stage 3: HOT older than 14 days -> WARM (60)
$PSQL -c "
UPDATE thermal_memory_archive
SET current_stage = 'WARM',
    temperature_score = 60,
    updated_at = NOW()
WHERE current_stage = 'HOT'
  AND created_at < NOW() - INTERVAL '14 days';
" 2>&1 | tee -a $LOG

# Stage 4: WARM older than 30 days -> COOL (40)
$PSQL -c "
UPDATE thermal_memory_archive
SET current_stage = 'COOL',
    temperature_score = 40,
    updated_at = NOW()
WHERE current_stage = 'WARM'
  AND created_at < NOW() - INTERVAL '30 days';
" 2>&1 | tee -a $LOG

# Stage 5: COOL older than 60 days -> COLD (20)
$PSQL -c "
UPDATE thermal_memory_archive
SET current_stage = 'COLD',
    temperature_score = 20,
    updated_at = NOW()
WHERE current_stage = 'COOL'
  AND created_at < NOW() - INTERVAL '60 days';
" 2>&1 | tee -a $LOG

# Stage 6: COLD older than 90 days -> ARCHIVE (10)
$PSQL -c "
UPDATE thermal_memory_archive
SET current_stage = 'ARCHIVE',
    temperature_score = 10,
    updated_at = NOW()
WHERE current_stage = 'COLD'
  AND created_at < NOW() - INTERVAL '90 days';
" 2>&1 | tee -a $LOG

# Report
echo "$(date): Decay complete. Summary:" >> $LOG
$PSQL -c "
SELECT current_stage, COUNT(*), AVG(temperature_score)::int as avg_temp
FROM thermal_memory_archive
GROUP BY current_stage
ORDER BY avg_temp DESC;
" 2>&1 | tee -a $LOG

echo "$(date): Pheromone decay v2 finished" >> $LOG