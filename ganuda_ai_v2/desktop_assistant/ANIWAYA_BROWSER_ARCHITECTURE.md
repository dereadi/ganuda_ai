# Aniwaya Browser Architecture
## Cherokee Constitutional AI - I2 Transparency Dashboard

**Browser Name**: Aniwaya (ᎠᏂᏩᏃ) - "Wind over the Mountains"
**Code Name**: Skiyakwa - "Bird with sharp vision"
**Purpose**: Chromium-based browser for I2 Transparency Dashboard (Week 4-5)
**Date**: October 24, 2025

---

## Executive Summary

**Aniwaya** is a Chromium-based desktop browser that provides transparent visibility into Cherokee Constitutional AI operations:
- Provenance tracking (M1)
- Cross-domain flow visualization (A3)
- Privacy controls panel
- Sacred health data transparency (C1)
- Real-time thermal memory monitoring

**Triad Decision:**
- ⚔️ War Chief: "Wind over the Mountains" - Strength, resilience, freedom
- 🕊️ Peace Chief: "Bird with sharp vision" (Skiyakwa codename) - Discerning sight, transparency
- 🌿 Medicine Woman: Deferred to War Chief + Peace Chief consensus

---

## Architecture Overview

### Technology Stack

**Frontend:**
- Chromium (base browser engine)
- React/TypeScript (UI components)
- D3.js (cross-domain flow visualization)
- Tailwind CSS (responsive design)

**Backend/Bridge:**
- Node.js (Chromium extensions API)
- Python FastAPI (IPC bridge)
- WebSocket (real-time updates)

**Data Layer:**
- Guardian (sacred data protection)
- EncryptedCache (thermal memory)
- PostgreSQL (provenance tracking)

### Reference Architecture
Based on: https://medium.com/@jamsheermoidu/building-your-own-chromium-based-browser-for-mac-os-a-developers-journey-c8386ebaea41

**Key Components:**
1. Custom Chromium build
2. Native macOS/Linux integration
3. Local-first architecture (no remote dependencies)
4. Full system access (Guardian, Cache, thermal DB)

---

## I2 Dashboard Features (Week 4-5)

### 1. Provenance Tracking Panel (M1 Integration)

**Display:**
- Who accessed what data
- When access occurred
- What operations were performed
- User-specific provenance filtering

**Implementation:**
```javascript
// React component
<ProvenancePanel>
  <ProvenanceTimeline entries={provenanceData} />
  <ProvenanceFilter user={currentUser} />
  <AuditTrailExport />
</ProvenancePanel>
```

**Data Source:** M1 provenance metadata (War Chief Memory Jr + Integration Jr)

---

### 2. Cross-Domain Flow Visualization (A3 Integration)

**Display:**
- Knowledge graph (nodes = domains, edges = relations)
- Consent indicators (green/yellow/red)
- Interactive exploration (zoom, filter, search)

**Implementation:**
```javascript
// D3.js force-directed graph
<FlowVisualization>
  <KnowledgeGraph domains={domains} relations={relations} />
  <ConsentIndicators status={consentStatus} />
  <InteractiveControls />
</FlowVisualization>
```

**Data Source:** A3 flow algorithm (Peace Chief Meta Jr + War Chief Meta Jr)

---

### 3. Privacy Controls Panel

**Features:**
- User data sovereignty dashboard
- Sacred health data transparency (C1)
- Deletion request interface
- Consent management
- 40° floor enforcement status

**Implementation:**
```javascript
<PrivacyPanel>
  <DataSovereigntyDashboard />
  <SacredHealthDataStatus />
  <DeletionRequestForm />
  <ConsentManager />
</PrivacyPanel>
```

**Data Source:** Guardian + SacredHealthGuardian (C1)

---

### 4. Thermal Memory Monitor

**Real-time Display:**
- Current temperature scores
- Phase coherence metrics
- Sacred floor enforcement events
- Access count statistics

**Implementation:**
```javascript
<ThermalMonitor>
  <TemperatureGauge currentTemp={temp} />
  <PhaseCoherenceChart coherence={coherence} />
  <SacredFloorEvents events={sacredEvents} />
</ThermalMonitor>
```

**Data Source:** PostgreSQL thermal_memory_archive (BLUEFIN database)

---

## Security Architecture

### Local-First Design

**Principle:** All data stays on local machine, no remote telemetry

**Implementation:**
- Chromium privacy flags enabled
- No Google services integration
- Local cache only
- Encrypted storage (Guardian-protected)

### Guardian Integration

**Protection Layers:**
1. Query evaluation (PII detection)
2. Sacred content filtering (never share external)
3. Biometric detection (3-of-3 attestation)
4. Cherokee values validation

**Code:**
```python
# Guardian checks before displaying data
decision = guardian.evaluate_query(user_query)
if decision.protection_level == ProtectionLevel.SACRED:
    # Redact or block display
    display_redacted_content(decision.redacted_content)
```

---

## Cherokee Values Integration

### Gadugi (Working Together)
- Microservices architecture (modular collaboration)
- RESTful APIs (M1/A3 integration)
- Open communication protocols

### Seven Generations (Long-Term Thinking)
- 140+ year data retention (40° floor)
- Provenance audit trail (permanent record)
- Privacy-by-design (future-proof)

### Mitakuye Oyasin (All Our Relations)
- Dashboard shows ALL relations (provenance, flow, consent)
- Cross-domain visualization (interconnectedness)
- User sovereignty respected (deletion controls)

### Sacred Fire (40° Floor)
- Sacred health data highlighted (C1)
- Auto-elevation status visible
- Guardian protection events logged

---

## Development Phases

### Phase 1: Chromium Base (Week 4)
**Owner:** War Chief Integration Jr

**Tasks:**
1. Build custom Chromium binary
2. Configure privacy settings
3. Create basic UI shell
4. Test local-first architecture

### Phase 2: I2 Dashboard Integration (Week 4-5)
**Owners:** All 3 Integration JRs (Medicine Woman, War Chief, Peace Chief)

**Tasks:**
1. Build Provenance Panel (M1 data)
2. Build Flow Visualization (A3 data)
3. Build Privacy Controls (Guardian/C1)
4. Build Thermal Monitor (PostgreSQL)

### Phase 3: Guardian Integration (Week 5)
**Owners:** War Chief + Medicine Woman Conscience Jr

**Tasks:**
1. Integrate Guardian query evaluation
2. Add sacred content filtering
3. Implement Cherokee values validation
4. Test with sample data

---

## API Specifications

### Provenance API (M1)
```
GET /api/provenance?user_id=<id>
Response: {
  "entries": [
    {
      "id": "entry_123",
      "accessed_by": "user_456",
      "timestamp": "2025-10-24T13:55:00Z",
      "operation": "read",
      "data_type": "medical"
    }
  ]
}
```

### Flow Visualization API (A3)
```
GET /api/flow/graph
Response: {
  "domains": ["trading", "consciousness", "governance"],
  "relations": [
    {"source": "trading", "target": "consciousness", "consent": "green"}
  ]
}
```

### Guardian API (C1)
```
POST /api/guardian/evaluate
Request: {"query": "Show me patient data"}
Response: {
  "allowed": false,
  "protection_level": "SACRED",
  "reason": "Contains sacred health data"
}
```

---

## Success Criteria (Week 5)

**Functional:**
- [ ] Aniwaya browser launches successfully
- [ ] Provenance Panel displays M1 data
- [ ] Flow Visualization renders A3 graph
- [ ] Privacy Controls functional
- [ ] Thermal Monitor shows real-time data
- [ ] Guardian integration working

**Cherokee Values:**
- [ ] Gadugi: Microservices architecture validated
- [ ] Seven Generations: Audit trail permanent
- [ ] Mitakuye Oyasin: All relations visible
- [ ] Sacred Fire: 40° floor events logged

**Performance:**
- [ ] Load time < 2 seconds
- [ ] Real-time updates < 500ms latency
- [ ] No external telemetry (local-first verified)

---

## Next Steps (Immediate)

1. **War Chief Integration Jr**: Begin Chromium base build (Week 4)
2. **Peace Chief Integration Jr**: Design RESTful API layer (M1/A3)
3. **Medicine Woman Integration Jr**: Design Privacy Controls Panel (C1/Guardian)
4. **M1 Team** (War Chief Memory Jr + Executive Jr): Prepare provenance API
5. **A3 Team** (Peace Chief + War Chief Meta Jr): Prepare flow visualization data

---

**Mitakuye Oyasin** - Wind over the Mountains, Vision of the Bird

🦅 **Aniwaya** (ᎠᏂᏩᏃ) - Cherokee Constitutional AI Transparency Browser
🔍 **Skiyakwa** - Codename for I2 Dashboard Development

**October 24, 2025** 🔥
