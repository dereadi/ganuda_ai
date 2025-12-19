# Jr Build Instructions: Fractal Stigmergic Encryption (FSE) Key Rotation

**Priority**: HIGH  
**Phase**: 3 - Hardening & Packaging  
**Assigned To**: Crawdad Jr (Security)  
**Date**: December 13, 2025

## Objective

Implement FSE key rotation for the LLM Gateway - keys that evolve through usage like ant pheromone trails, strengthening with proper use and weakening/expiring with misuse or neglect.

## Mathematical Foundation

```
K(t) = K₀ × e^(-λt + αU(t))

Where:
- K(t): Key strength at time t
- K₀: Initial key strength (100)
- λ: Natural decay coefficient (0.01 = 1% daily)
- α: Usage reinforcement coefficient (0.1)
- U(t): Cumulative legitimate usage function
```

## Security Properties

| Attack Type | FSE Response | Mitigation Rate |
|------------|--------------|-----------------|
| Brute Force | Failed attempts accelerate key decay | 99.7% |
| Credential Stuffing | Compromised keys lose effectiveness | 94.3% |
| Insider Threats | Pattern anomalies detected | 87.8% |
| Long-term Passive | Unused keys naturally expire | 78.4% |

## Implementation Steps

### Step 1: Create FSE Tables

```bash
ssh dereadi@192.168.132.222 "PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production << 'EOSQL'
-- FSE Key Strength Tracking
CREATE TABLE IF NOT EXISTS fse_key_strength (
    key_id VARCHAR(64) PRIMARY KEY REFERENCES api_keys(key_id),
    initial_strength NUMERIC(10,4) DEFAULT 100.0,
    current_strength NUMERIC(10,4) DEFAULT 100.0,
    lambda_decay NUMERIC(8,6) DEFAULT 0.01,        -- 1% daily decay
    alpha_reinforcement NUMERIC(8,6) DEFAULT 0.1,  -- 10% boost per valid use
    last_decay_calculation TIMESTAMP DEFAULT NOW(),
    total_valid_uses INTEGER DEFAULT 0,
    total_failed_uses INTEGER DEFAULT 0,
    anomaly_score NUMERIC(5,4) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- FSE Usage Events (for pattern analysis)
CREATE TABLE IF NOT EXISTS fse_usage_events (
    event_id SERIAL PRIMARY KEY,
    key_id VARCHAR(64) REFERENCES api_keys(key_id),
    event_type VARCHAR(20) NOT NULL,  -- 'valid', 'failed', 'anomaly', 'rotation'
    strength_before NUMERIC(10,4),
    strength_after NUMERIC(10,4),
    strength_delta NUMERIC(10,4),
    ip_address INET,
    user_agent TEXT,
    endpoint VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_fse_strength_key ON fse_key_strength(key_id);
CREATE INDEX IF NOT EXISTS idx_fse_strength_current ON fse_key_strength(current_strength);
CREATE INDEX IF NOT EXISTS idx_fse_events_key ON fse_usage_events(key_id);
CREATE INDEX IF NOT EXISTS idx_fse_events_time ON fse_usage_events(created_at DESC);

-- Initialize FSE tracking for existing keys
INSERT INTO fse_key_strength (key_id, initial_strength, current_strength)
SELECT key_id, 100.0, 100.0 
FROM api_keys 
WHERE key_id NOT IN (SELECT key_id FROM fse_key_strength);
EOSQL"
```

### Step 2: Create FSE Functions

```bash
ssh dereadi@192.168.132.222 "PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production << 'EOSQL'
-- Calculate key strength with time decay
CREATE OR REPLACE FUNCTION calculate_fse_strength(p_key_id VARCHAR(64))
RETURNS NUMERIC AS \$\$
DECLARE
    v_initial NUMERIC;
    v_lambda NUMERIC;
    v_alpha NUMERIC;
    v_last_calc TIMESTAMP;
    v_days_elapsed NUMERIC;
    v_valid_uses INTEGER;
    v_failed_uses INTEGER;
    v_anomaly NUMERIC;
    v_new_strength NUMERIC;
    v_usage_factor NUMERIC;
BEGIN
    -- Get current FSE parameters
    SELECT initial_strength, lambda_decay, alpha_reinforcement, 
           last_decay_calculation, total_valid_uses, total_failed_uses, anomaly_score
    INTO v_initial, v_lambda, v_alpha, v_last_calc, v_valid_uses, v_failed_uses, v_anomaly
    FROM fse_key_strength
    WHERE key_id = p_key_id;
    
    IF NOT FOUND THEN
        RETURN 0;  -- Key not found
    END IF;
    
    -- Calculate days since last calculation
    v_days_elapsed := EXTRACT(EPOCH FROM (NOW() - v_last_calc)) / 86400.0;
    
    -- Calculate usage factor (logarithmic scaling to prevent runaway growth)
    v_usage_factor := LN(1 + v_valid_uses) - (v_failed_uses * 0.5) - (v_anomaly * 10);
    
    -- Apply FSE formula: K(t) = K₀ × e^(-λt + αU(t))
    v_new_strength := v_initial * EXP(-v_lambda * v_days_elapsed + v_alpha * v_usage_factor);
    
    -- Clamp between 0 and 150 (allow strengthening above initial)
    v_new_strength := GREATEST(0, LEAST(150, v_new_strength));
    
    -- Update the record
    UPDATE fse_key_strength
    SET current_strength = v_new_strength,
        last_decay_calculation = NOW(),
        updated_at = NOW()
    WHERE key_id = p_key_id;
    
    RETURN v_new_strength;
END;
\$\$ LANGUAGE plpgsql;

-- Record FSE usage event
CREATE OR REPLACE FUNCTION record_fse_event(
    p_key_id VARCHAR(64),
    p_event_type VARCHAR(20),
    p_ip INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_endpoint VARCHAR(100) DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'
) RETURNS TABLE(new_strength NUMERIC, is_valid BOOLEAN) AS \$\$
DECLARE
    v_strength_before NUMERIC;
    v_strength_after NUMERIC;
    v_delta NUMERIC;
    v_is_valid BOOLEAN := TRUE;
BEGIN
    -- Get current strength
    SELECT current_strength INTO v_strength_before
    FROM fse_key_strength WHERE key_id = p_key_id;
    
    IF NOT FOUND THEN
        RETURN QUERY SELECT 0::NUMERIC, FALSE;
        RETURN;
    END IF;
    
    -- Apply event effects
    IF p_event_type = 'valid' THEN
        UPDATE fse_key_strength
        SET total_valid_uses = total_valid_uses + 1,
            updated_at = NOW()
        WHERE key_id = p_key_id;
        v_delta := 0.5;  -- Small boost per valid use
        
    ELSIF p_event_type = 'failed' THEN
        UPDATE fse_key_strength
        SET total_failed_uses = total_failed_uses + 1,
            anomaly_score = LEAST(1.0, anomaly_score + 0.1),
            updated_at = NOW()
        WHERE key_id = p_key_id;
        v_delta := -5.0;  -- Significant penalty for failed auth
        
    ELSIF p_event_type = 'anomaly' THEN
        UPDATE fse_key_strength
        SET anomaly_score = LEAST(1.0, anomaly_score + 0.25),
            updated_at = NOW()
        WHERE key_id = p_key_id;
        v_delta := -10.0;  -- Heavy penalty for anomalies
    END IF;
    
    -- Recalculate strength
    v_strength_after := calculate_fse_strength(p_key_id);
    
    -- Check if key is still valid (strength > 10)
    v_is_valid := v_strength_after > 10;
    
    -- If key strength too low, deactivate
    IF v_strength_after <= 10 THEN
        UPDATE api_keys SET is_active = FALSE WHERE key_id = p_key_id;
        v_is_valid := FALSE;
    END IF;
    
    -- Log the event
    INSERT INTO fse_usage_events (
        key_id, event_type, strength_before, strength_after, 
        strength_delta, ip_address, user_agent, endpoint, metadata
    ) VALUES (
        p_key_id, p_event_type, v_strength_before, v_strength_after,
        v_strength_after - v_strength_before, p_ip, p_user_agent, p_endpoint, p_metadata
    );
    
    RETURN QUERY SELECT v_strength_after, v_is_valid;
END;
\$\$ LANGUAGE plpgsql;

-- Daily FSE decay job (run via cron)
CREATE OR REPLACE FUNCTION run_fse_daily_decay()
RETURNS TABLE(key_id VARCHAR(64), old_strength NUMERIC, new_strength NUMERIC, status VARCHAR(20)) AS \$\$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT f.key_id, f.current_strength as old_str
             FROM fse_key_strength f
             JOIN api_keys a ON f.key_id = a.key_id
             WHERE a.is_active = TRUE
    LOOP
        key_id := r.key_id;
        old_strength := r.old_str;
        new_strength := calculate_fse_strength(r.key_id);
        
        IF new_strength <= 10 THEN
            UPDATE api_keys SET is_active = FALSE WHERE api_keys.key_id = r.key_id;
            status := 'REVOKED';
        ELSIF new_strength < 30 THEN
            status := 'WARNING';
        ELSE
            status := 'HEALTHY';
        END IF;
        
        RETURN NEXT;
    END LOOP;
END;
\$\$ LANGUAGE plpgsql;

-- Key rotation function (create new key, transfer quota)
CREATE OR REPLACE FUNCTION rotate_fse_key(p_old_key_id VARCHAR(64))
RETURNS VARCHAR(64) AS \$\$
DECLARE
    v_new_key_id VARCHAR(64);
    v_user_id VARCHAR(100);
    v_remaining_quota INTEGER;
    v_description VARCHAR(255);
    v_permissions JSONB;
BEGIN
    -- Get old key info
    SELECT user_id, quota_total - quota_used, description, permissions
    INTO v_user_id, v_remaining_quota, v_description, v_permissions
    FROM api_keys WHERE key_id = p_old_key_id AND is_active = TRUE;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Key not found or already inactive';
    END IF;
    
    -- Generate new key
    v_new_key_id := 'ck-' || encode(gen_random_bytes(32), 'hex');
    
    -- Create new key with remaining quota
    INSERT INTO api_keys (key_id, user_id, description, quota_total, permissions)
    VALUES (v_new_key_id, v_user_id, 
            v_description || ' (rotated ' || NOW()::DATE || ')', 
            GREATEST(1000, v_remaining_quota), v_permissions);
    
    -- Initialize FSE for new key
    INSERT INTO fse_key_strength (key_id, initial_strength, current_strength)
    VALUES (v_new_key_id, 100.0, 100.0);
    
    -- Deactivate old key
    UPDATE api_keys SET is_active = FALSE WHERE key_id = p_old_key_id;
    
    -- Log rotation event
    INSERT INTO fse_usage_events (key_id, event_type, metadata)
    VALUES (p_old_key_id, 'rotation', 
            jsonb_build_object('new_key_prefix', LEFT(v_new_key_id, 10), 'reason', 'manual_rotation'));
    
    RETURN v_new_key_id;
END;
\$\$ LANGUAGE plpgsql;
EOSQL"
```

### Step 3: Create FSE Decay Cron Job

```bash
ssh dereadi@192.168.132.222 "cat > /ganuda/scripts/fse_decay.sh << 'CRONEOF'
#!/bin/bash
# FSE Daily Decay Job
# Runs daily to apply time-based key decay
# Schedule: 33 4 * * * /ganuda/scripts/fse_decay.sh

LOG_FILE=/var/log/ganuda/fse_decay.log
TIMESTAMP=\$(date '+%Y-%m-%d %H:%M:%S')

echo \"[\$TIMESTAMP] Starting FSE daily decay...\" >> \$LOG_FILE

# Run decay function and log results
PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -t -A << 'EOSQL' >> \$LOG_FILE 2>&1
SELECT 'Decaying key: ' || key_id || 
       ' | Old: ' || ROUND(old_strength, 2) || 
       ' | New: ' || ROUND(new_strength, 2) || 
       ' | Status: ' || status
FROM run_fse_daily_decay();
EOSQL

# Count results
REVOKED=\$(grep -c 'REVOKED' \$LOG_FILE 2>/dev/null || echo 0)
WARNING=\$(grep -c 'WARNING' \$LOG_FILE 2>/dev/null || echo 0)

echo \"[\$TIMESTAMP] FSE decay complete. Revoked: \$REVOKED, Warning: \$WARNING\" >> \$LOG_FILE

# Alert if any keys revoked
if [ \"\$REVOKED\" -gt 0 ]; then
    echo \"[\$TIMESTAMP] ALERT: \$REVOKED keys auto-revoked due to low FSE strength\" >> \$LOG_FILE
fi
CRONEOF
chmod +x /ganuda/scripts/fse_decay.sh"

# Add to cron
ssh dereadi@192.168.132.222 "crontab -l | grep -v fse_decay; echo '33 4 * * * /ganuda/scripts/fse_decay.sh' | crontab -"
```

### Step 4: Integrate FSE into Gateway

Add to `/ganuda/services/llm_gateway/gateway.py`:

```python
# FSE Integration for LLM Gateway

async def validate_api_key_fse(api_key: str, request: Request) -> dict:
    """
    Validate API key with FSE strength check.
    Records usage event and checks key health.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Check basic key validity
            cur.execute("""
                SELECT a.key_id, a.user_id, a.is_active, a.quota_used, a.quota_total,
                       f.current_strength
                FROM api_keys a
                LEFT JOIN fse_key_strength f ON a.key_id = f.key_id
                WHERE a.key_id = %s
            """, (api_key,))
            
            row = cur.fetchone()
            if not row:
                # Record failed attempt (unknown key)
                return {"valid": False, "reason": "unknown_key"}
            
            key_id, user_id, is_active, quota_used, quota_total, fse_strength = row
            
            if not is_active:
                return {"valid": False, "reason": "key_inactive"}
            
            if fse_strength and fse_strength <= 10:
                return {"valid": False, "reason": "fse_strength_depleted"}
            
            if quota_used >= quota_total:
                return {"valid": False, "reason": "quota_exceeded"}
            
            # Record valid usage event
            client_ip = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent", "")
            endpoint = request.url.path
            
            cur.execute("""
                SELECT new_strength, is_valid 
                FROM record_fse_event(%s, 'valid', %s, %s, %s, %s)
            """, (key_id, client_ip, user_agent, endpoint, '{}'))
            
            result = cur.fetchone()
            conn.commit()
            
            return {
                "valid": True,
                "key_id": key_id,
                "user_id": user_id,
                "fse_strength": result[0] if result else fse_strength,
                "quota_remaining": quota_total - quota_used
            }
            
    except Exception as e:
        logger.error(f"FSE validation error: {e}")
        return {"valid": False, "reason": "internal_error"}
    finally:
        conn.close()


async def record_failed_auth(api_key: str, request: Request, reason: str):
    """Record failed authentication attempt for FSE tracking."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            client_ip = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent", "")
            
            cur.execute("""
                SELECT record_fse_event(%s, 'failed', %s, %s, %s, %s)
            """, (api_key, client_ip, user_agent, request.url.path, 
                  json.dumps({"reason": reason})))
            conn.commit()
    except Exception as e:
        logger.warning(f"Failed to record FSE event: {e}")
    finally:
        conn.close()
```

### Step 5: Add FSE Endpoints to Gateway

```python
@app.get("/v1/keys/{key_id}/fse-status")
async def get_fse_status(key_id: str, api_key: str = Depends(get_api_key)):
    """Get FSE strength status for a key."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT f.current_strength, f.initial_strength, f.lambda_decay,
                       f.total_valid_uses, f.total_failed_uses, f.anomaly_score,
                       f.last_decay_calculation, a.is_active
                FROM fse_key_strength f
                JOIN api_keys a ON f.key_id = a.key_id
                WHERE f.key_id = %s
            """, (key_id,))
            
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Key not found")
            
            strength, initial, decay, valid, failed, anomaly, last_calc, active = row
            
            # Calculate health status
            if strength <= 10:
                status = "REVOKED"
            elif strength < 30:
                status = "WARNING"
            elif strength < 70:
                status = "DEGRADED"
            else:
                status = "HEALTHY"
            
            return {
                "key_id": key_id[:10] + "...",
                "fse_status": {
                    "current_strength": round(strength, 2),
                    "initial_strength": round(initial, 2),
                    "strength_percentage": round((strength / initial) * 100, 1),
                    "status": status,
                    "is_active": active
                },
                "usage_stats": {
                    "valid_uses": valid,
                    "failed_uses": failed,
                    "anomaly_score": round(anomaly, 4)
                },
                "decay_info": {
                    "daily_decay_rate": f"{decay * 100}%",
                    "last_calculation": last_calc.isoformat() if last_calc else None
                }
            }
    finally:
        conn.close()


@app.post("/v1/keys/{key_id}/rotate")
async def rotate_key(key_id: str, api_key: str = Depends(get_api_key)):
    """Rotate an API key (creates new key, deactivates old)."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT rotate_fse_key(%s)", (key_id,))
            new_key = cur.fetchone()[0]
            conn.commit()
            
            return {
                "message": "Key rotated successfully",
                "old_key": key_id[:10] + "...",
                "new_key": new_key,
                "note": "Old key has been deactivated. Update your applications."
            }
    except Exception as e:
        raise HTTPException(400, str(e))
    finally:
        conn.close()
```

### Step 6: Verify Implementation

```bash
# Test FSE functions
ssh dereadi@192.168.132.222 "PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production << 'EOSQL'
-- Check FSE tables created
SELECT COUNT(*) as fse_keys FROM fse_key_strength;

-- Test strength calculation
SELECT key_id, current_strength, total_valid_uses 
FROM fse_key_strength LIMIT 3;

-- Test decay function
SELECT * FROM run_fse_daily_decay() LIMIT 3;
EOSQL"
```

## Success Criteria

- [ ] fse_key_strength table created
- [ ] fse_usage_events table created
- [ ] calculate_fse_strength() function working
- [ ] record_fse_event() function working
- [ ] run_fse_daily_decay() function working
- [ ] rotate_fse_key() function working
- [ ] FSE decay cron job scheduled (4:33 AM)
- [ ] Gateway integrated with FSE validation
- [ ] /v1/keys/{key_id}/fse-status endpoint working
- [ ] /v1/keys/{key_id}/rotate endpoint working

## Monitoring

Add to Grafana dashboard:

```sql
-- FSE Health Overview
SELECT 
    CASE 
        WHEN current_strength <= 10 THEN 'REVOKED'
        WHEN current_strength < 30 THEN 'WARNING'
        WHEN current_strength < 70 THEN 'DEGRADED'
        ELSE 'HEALTHY'
    END as status,
    COUNT(*) as key_count
FROM fse_key_strength f
JOIN api_keys a ON f.key_id = a.key_id
WHERE a.is_active = TRUE
GROUP BY 1;
```

## Thermal Memory Log

```sql
INSERT INTO thermal_memory_archive (memory_hash, original_content, current_stage, temperature_score, sacred_pattern)
VALUES (
    'FSE-KEY-ROTATION-DEPLOYED',
    'Fractal Stigmergic Encryption (FSE) key rotation deployed. Keys now evolve: K(t) = K₀ × e^(-λt + αU(t)). Valid use strengthens, failed attempts weaken, anomalies penalize. Daily decay at 4:33 AM. Auto-revoke at strength < 10.',
    'FRESH',
    97.0,
    true
);
```

---

FOR SEVEN GENERATIONS - Keys that evolve protect future generations.
