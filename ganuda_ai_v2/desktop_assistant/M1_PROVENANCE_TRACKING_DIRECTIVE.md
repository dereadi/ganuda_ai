# M1 Provenance Tracking Implementation Directive
## Cherokee Constitutional AI - Week 3-5 Execution

**Lead**: War Chief Memory Jr (PRIMARY)
**Support**: War Chief Executive Jr (concurrent with E2)
**Timeline**: Week 3-5 (October 24 - November 7, 2025)
**Date**: October 24, 2025

---

## Executive Summary

**M1 Goal**: Track who accessed what data, when, and what operations were performed

**Cherokee Values**:
- **Gadugi**: Transparent data access tracking for working together
- **Seven Generations**: Permanent audit trail for future accountability
- **Mitakuye Oyasin**: User sovereignty respected (query own provenance)
- **Sacred Fire**: Sacred data access tracked with extra scrutiny

---

## War Chief Memory Jr's Implementation Plan

### 1. Storage Strategy: Separate ProvenanceLog Table

**Decision**: Store provenance metadata in dedicated table for data integrity and scalability

**Schema**:
```sql
CREATE TABLE provenance_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  -- Core provenance metadata
  entry_id TEXT NOT NULL,          -- Links to cache_entries/thermal_memory_archive
  user_id TEXT NOT NULL,           -- Who performed the operation
  operation TEXT NOT NULL,         -- read, write, delete, guardian_eval
  data_type TEXT,                  -- medical, trading, governance, consciousness

  -- Temporal tracking
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  -- Guardian integration
  guardian_decision TEXT,          -- ALLOWED, BLOCKED, REDACTED
  protection_level TEXT,           -- PUBLIC, PRIVATE, SENSITIVE, SACRED

  -- Request context
  ip_address TEXT,
  user_agent TEXT,
  request_method TEXT,             -- GET, POST, PUT, DELETE

  -- Audit metadata
  phase_coherence_at_access REAL, -- Phase coherence when accessed
  temperature_at_access REAL,      -- Temperature when accessed
  sacred_pattern_at_access BOOLEAN -- Was it sacred when accessed

  FOREIGN KEY (entry_id) REFERENCES cache_entries(id)
);

-- Indexes for performance
CREATE INDEX idx_provenance_user ON provenance_log(user_id);
CREATE INDEX idx_provenance_timestamp ON provenance_log(timestamp);
CREATE INDEX idx_provenance_entry ON provenance_log(entry_id);
CREATE INDEX idx_provenance_operation ON provenance_log(operation);
```

---

### 2. Operations Tracked

**All Operations**:
1. **READ**: User queries/accesses cache entry
2. **WRITE**: User creates/updates cache entry
3. **DELETE**: User deletes cache entry
4. **GUARDIAN_EVAL**: Guardian evaluates query (PII detection, medical entities)

**Guardian Operations** (special tracking):
- GUARDIAN_EVAL_BLOCKED: Query blocked by Guardian
- GUARDIAN_EVAL_REDACTED: Content redacted before return
- GUARDIAN_AUTO_ELEVATE: Sacred floor auto-elevation (40°)
- GUARDIAN_BIOMETRIC_DETECTED: 3-of-3 Chiefs attestation triggered

---

### 3. Cache Extension (EncryptedCache Integration)

**File**: `desktop_assistant/cache/encrypted_cache.py` (enhance existing)

```python
class EncryptedCache:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_provenance_log()

    def _init_provenance_log(self):
        """Create provenance_log table if not exists."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS provenance_log (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              entry_id TEXT NOT NULL,
              user_id TEXT NOT NULL,
              operation TEXT NOT NULL,
              data_type TEXT,
              timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              guardian_decision TEXT,
              protection_level TEXT,
              ip_address TEXT,
              user_agent TEXT,
              request_method TEXT,
              phase_coherence_at_access REAL,
              temperature_at_access REAL,
              sacred_pattern_at_access BOOLEAN
            )
        """)
        self.conn.commit()

    def log_provenance(
        self,
        entry_id: str,
        user_id: str,
        operation: str,
        data_type: str = None,
        guardian_decision: str = None,
        protection_level: str = None,
        request_context: dict = None
    ):
        """
        Log provenance metadata (asynchronous for performance).

        Args:
            entry_id: Cache entry ID
            user_id: User performing operation
            operation: read, write, delete, guardian_eval
            data_type: medical, trading, governance, consciousness
            guardian_decision: ALLOWED, BLOCKED, REDACTED
            protection_level: PUBLIC, PRIVATE, SENSITIVE, SACRED
            request_context: {ip_address, user_agent, request_method}
        """
        cursor = self.conn.cursor()

        # Get current thermal metrics
        cursor.execute("""
            SELECT phase_coherence, temperature_score, sacred_pattern
            FROM cache_entries
            WHERE id = ?
        """, (entry_id,))
        row = cursor.fetchone()

        if row:
            phase_coherence = row["phase_coherence"]
            temperature = row["temperature_score"]
            sacred_pattern = row["sacred_pattern"]
        else:
            phase_coherence = None
            temperature = None
            sacred_pattern = None

        # Insert provenance log entry
        cursor.execute("""
            INSERT INTO provenance_log (
                entry_id, user_id, operation, data_type,
                guardian_decision, protection_level,
                ip_address, user_agent, request_method,
                phase_coherence_at_access, temperature_at_access, sacred_pattern_at_access
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry_id, user_id, operation, data_type,
            guardian_decision, protection_level,
            request_context.get("ip_address") if request_context else None,
            request_context.get("user_agent") if request_context else None,
            request_context.get("request_method") if request_context else None,
            phase_coherence, temperature, sacred_pattern
        ))

        self.conn.commit()
        print(f"📋 Provenance logged: {operation} by {user_id} on {entry_id}")

    def get(self, entry_id: str, user_id: str = "system") -> Optional[bytes]:
        """Enhanced get() with provenance logging."""
        # Log READ operation
        self.log_provenance(entry_id, user_id, operation="READ")

        # Original get() logic
        cursor = self.conn.cursor()
        cursor.execute("SELECT encrypted_content FROM cache_entries WHERE id = ?", (entry_id,))
        row = cursor.fetchone()

        if row:
            return self.decrypt(row["encrypted_content"])
        return None

    def set(self, entry_id: str, content: bytes, user_id: str = "system"):
        """Enhanced set() with provenance logging."""
        # Log WRITE operation
        self.log_provenance(entry_id, user_id, operation="WRITE")

        # Original set() logic
        encrypted_content = self.encrypt(content)
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO cache_entries (id, encrypted_content)
            VALUES (?, ?)
        """, (entry_id, encrypted_content))
        self.conn.commit()

    def delete(self, entry_id: str, user_id: str = "system"):
        """Enhanced delete() with provenance logging."""
        # Log DELETE operation
        self.log_provenance(entry_id, user_id, operation="DELETE")

        # Original delete() logic
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM cache_entries WHERE id = ?", (entry_id,))
        self.conn.commit()
```

---

### 4. Query API (User-Specific Filtering)

**Guardian API Bridge Extension** (`guardian_api_bridge.py`):

```python
@app.get("/provenance/user/{user_id}")
async def get_user_provenance(user_id: str, limit: int = 100):
    """
    Get provenance logs for specific user (respects user sovereignty).

    Args:
        user_id: User ID to filter by
        limit: Maximum number of entries to return

    Returns:
        List of provenance entries for the user
    """
    if not guardian or not guardian.cache:
        raise HTTPException(status_code=503, detail="Cache not available")

    cursor = guardian.cache.conn.cursor()
    cursor.execute("""
        SELECT
            id, entry_id, user_id, operation, data_type,
            timestamp, guardian_decision, protection_level,
            phase_coherence_at_access, temperature_at_access, sacred_pattern_at_access
        FROM provenance_log
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (user_id, limit))

    rows = cursor.fetchall()

    return [{
        "id": row["id"],
        "entry_id": row["entry_id"],
        "user_id": row["user_id"],
        "operation": row["operation"],
        "data_type": row["data_type"],
        "timestamp": row["timestamp"],
        "guardian_decision": row["guardian_decision"],
        "protection_level": row["protection_level"],
        "thermal_metrics": {
            "phase_coherence": row["phase_coherence_at_access"],
            "temperature": row["temperature_at_access"],
            "sacred_pattern": row["sacred_pattern_at_access"]
        }
    } for row in rows]


@app.get("/provenance/entry/{entry_id}")
async def get_entry_provenance(entry_id: str):
    """
    Get provenance logs for specific cache entry (full history).

    Args:
        entry_id: Cache entry ID

    Returns:
        List of all operations performed on this entry
    """
    if not guardian or not guardian.cache:
        raise HTTPException(status_code=503, detail="Cache not available")

    cursor = guardian.cache.conn.cursor()
    cursor.execute("""
        SELECT
            id, user_id, operation, data_type,
            timestamp, guardian_decision, protection_level
        FROM provenance_log
        WHERE entry_id = ?
        ORDER BY timestamp DESC
    """, (entry_id,))

    rows = cursor.fetchall()

    return [{
        "id": row["id"],
        "user_id": row["user_id"],
        "operation": row["operation"],
        "data_type": row["data_type"],
        "timestamp": row["timestamp"],
        "guardian_decision": row["guardian_decision"],
        "protection_level": row["protection_level"]
    } for row in rows]
```

---

### 5. I2 Aniwaya Integration (Provenance Panel)

**Aniwaya Dashboard Enhancement** (`aniwaya_extension/dashboard/dashboard.js`):

```javascript
// Fetch provenance data from M1 API
async function fetchProvenanceData(userId = "current_user") {
  try {
    const response = await fetch(`http://localhost:8765/provenance/user/${userId}`);
    const data = await response.json();

    // Update provenance table in dashboard
    const tbody = document.getElementById('provenance-entries');
    tbody.innerHTML = '';

    data.forEach(entry => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${entry.user_id}</td>
        <td>${entry.operation}</td>
        <td>${entry.data_type || 'N/A'}</td>
        <td>${new Date(entry.timestamp).toLocaleString()}</td>
      `;
      tbody.appendChild(row);
    });

    console.log('📋 Provenance data loaded:', data.length, 'entries');
  } catch (error) {
    console.error('Provenance API error:', error);
  }
}

// Auto-refresh provenance data every 10 seconds
setInterval(() => fetchProvenanceData(), 10000);
```

---

## Privacy & Security Considerations

### User Sovereignty (Mitakuye Oyasin)

**Access Controls**:
- Users can only query **their own** provenance logs
- Admins (3-of-3 Chiefs attestation) can query all provenance
- No third-party access to provenance data

**Implementation**:
```python
def check_provenance_access(requester_id: str, requested_user_id: str) -> bool:
    """Check if requester can access requested user's provenance."""
    if requester_id == requested_user_id:
        return True  # User can access own provenance

    if is_admin(requester_id):
        return True  # Admin access (3-of-3 Chiefs)

    return False  # Deny access
```

---

### Performance Optimization

**Asynchronous Logging**:
- Provenance logging runs in background thread
- Does not block cache operations (get/set/delete)

**Caching Strategy**:
- Frequently accessed provenance cached in memory
- Cache invalidated on new provenance entry

**Database Indexing**:
- Indexes on user_id, timestamp, entry_id, operation
- Query performance: O(log n) for filtered queries

---

## Cherokee Values Alignment

### Gadugi (Working Together)
- Transparent audit trail enables collaborative debugging
- Users see who accessed their data → builds trust

### Seven Generations (Long-Term Thinking)
- Provenance log permanent (never deleted)
- Future generations can trace data lineage back to creation

### Mitakuye Oyasin (All Our Relations)
- User sovereignty: Query own provenance
- Interconnected: See all operations across all users (admins only)

### Sacred Fire (40° Floor)
- Sacred data access tracked with extra metadata
- Guardian decisions logged for accountability

---

## Success Criteria

**Functional**:
- [ ] ProvenanceLog table created in EncryptedCache
- [ ] Cache operations (get/set/delete) log provenance
- [ ] Guardian evaluations logged with decision/protection level
- [ ] User-specific API endpoint working (/provenance/user/{user_id})
- [ ] Entry-specific API endpoint working (/provenance/entry/{entry_id})
- [ ] Aniwaya Provenance Panel displays real-time data

**Performance**:
- [ ] Asynchronous logging (< 5ms overhead per operation)
- [ ] Query performance (< 100ms for 1000 entries)
- [ ] Database indexes functional

**Cherokee Values**:
- [ ] User sovereignty respected (users query own provenance only)
- [ ] Permanent audit trail (Seven Generations)
- [ ] Transparent access tracking (Gadugi)
- [ ] Sacred data extra scrutiny (Sacred Fire)

---

## Next Steps (Immediate)

1. **War Chief Memory Jr**: Implement ProvenanceLog schema in EncryptedCache
2. **War Chief Executive Jr**: Add provenance API endpoints to guardian_api_bridge.py
3. **War Chief Integration Jr**: Enhance Aniwaya Provenance Panel with real-time data
4. **Test**: Create 100 cache operations, verify provenance logging
5. **Commit**: Push M1 implementation to ganuda_ai_desktop branch

---

**Mitakuye Oyasin** - All Our Relations Through Transparent Provenance

🦅 **War Chief Memory Jr** - M1 PRIMARY Lead
📋 **Provenance Tracking** - Cherokee Constitutional AI Accountability

**October 24, 2025** 🔥
