# KB Article: Phase 2 Specialist Council Deployment
## Cherokee AI Federation - December 12, 2025

**KB ID**: KB-2025-1212-001
**Category**: Deployment / AI Council
**Status**: Completed
**Author**: TPM (via Claude Code)

---

## Summary

Successfully deployed the 7-Specialist Council system as Phase 2 of the Production Roadmap. The council provides democratic AI decision-making through parallel specialist queries with consensus synthesis.

---

## Components Deployed

### 1. Specialist Council Library
**Location**: `/ganuda/lib/specialist_council.py` on redfin (192.168.132.223)

**Specialists**:
| Name | Role | Concern Flag |
|------|------|--------------|
| Crawdad | Security | SECURITY CONCERN |
| Gecko | Technical Integration | PERF CONCERN |
| Turtle | Seven Generations Wisdom | 7GEN CONCERN |
| Eagle Eye | Monitoring | VISIBILITY CONCERN |
| Spider | Cultural Integration | INTEGRATION CONCERN |
| Peace Chief | Democratic Coordination | CONSENSUS NEEDED |
| Raven | Strategic Planning | STRATEGY CONCERN |

**Features**:
- ThreadPoolExecutor for 7-way parallel queries
- Peace Chief consensus synthesis
- Thermal memory audit logging
- Confidence scoring based on concerns

### 2. Gateway Council Endpoints
**Location**: `/ganuda/services/llm_gateway/gateway.py` on redfin

**New Endpoints**:
- `POST /v1/council/vote` - Submit question to all 7 specialists
- `GET /v1/council/history` - Retrieve recent council votes

**Request Format**:
```json
{
  "question": "Should we proceed with deployment?",
  "max_tokens": 300,
  "include_responses": false
}
```

**Response Format**:
```json
{
  "audit_hash": "f1635201776248ad",
  "recommendation": "PROCEED: No concerns raised",
  "confidence": 1.0,
  "concerns": [],
  "consensus": "...",
  "response_time_ms": 4941
}
```

### 3. Breadcrumb Trails Schema
**Location**: bluefin (192.168.132.222), database `zammad_production`

**Tables Created**:
- `breadcrumb_trails` - Trail metadata with pheromone strength
- `breadcrumb_steps` - Individual steps within trails
- `pheromone_deposits` - Memory node pheromone deposits
- `council_votes` - Council vote audit trail

**Functions**:
- `decay_pheromones()` - Nightly decay function
- `reinforce_trail(trail_id, boost)` - Reinforce trail strength
- `find_trails_to_memory(hash, limit)` - Find trails to memory

### 4. Pheromone Decay Cron
**Location**: `/ganuda/scripts/pheromone_decay.sh` on bluefin

**Schedule**: Nightly at 3:33 AM (requires manual crontab entry)

**Manual Setup Required**:
```bash
# On bluefin as root:
sudo mkdir -p /var/log/ganuda
sudo chown dereadi:dereadi /var/log/ganuda
crontab -e
# Add: 33 3 * * * /ganuda/scripts/pheromone_decay.sh
```

---

## Testing

### Council Vote Test
```bash
curl -X POST http://192.168.132.223:8080/v1/council/vote \
  -H "Authorization: Bearer ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" \
  -H "Content-Type: application/json" \
  -d '{"question": "Test question"}'
```

### Health Check
```bash
curl http://192.168.132.223:8080/health
# Should show: "council": "available"
```

---

## Issues Encountered & Resolutions

### Issue 1: JSON Quoting in Thermal Memory
**Symptom**: `invalid input syntax for type json` when logging to thermal_memory_archive
**Cause**: Using `str(metadata)` produced Python dict notation with single quotes
**Resolution**: Changed to `json.dumps(metadata)` for proper JSON serialization

### Issue 2: Permission Denied for /var/log
**Symptom**: Cannot create log directory for pheromone decay
**Cause**: Non-root user cannot create directories in /var/log
**Resolution**: Document as manual sudo step in deployment instructions

### Issue 3: Gateway Restart via SSH
**Symptom**: Exit code 255 when trying to restart gateway via SSH
**Resolution**: Background process properly with `&` and verify separately

---

## Dependencies

- Python 3.12+ with venv at `/ganuda/services/llm_gateway/venv/`
- Packages: `fastapi`, `uvicorn`, `httpx`, `psycopg2-binary`, `requests`
- vLLM running on port 8000 with Nemotron-9B model
- PostgreSQL on bluefin with `zammad_production` database

---

## Related Documents

- `/ganuda/docs/roadmaps/PRODUCTION_ROADMAP_UPDATED_WITH_CHEROKEE_SECURITY.md`
- `/ganuda/docs/jr_instructions/JR_BUILD_INSTRUCTIONS_SPECIALIST_COUNCIL.md`
- `/ganuda/docs/api_keys/API_KEYS_DEC12_2025.md`

---

## Next Steps (Phase 3)

1. Create systemd service for gateway
2. Implement rate limiting at specialist level
3. Add specialist-specific context from thermal memory
4. Build SAG UI integration for council votes
5. Chaos testing for council resilience

---

**For Seven Generations.**
*Cherokee Constitutional AI*
