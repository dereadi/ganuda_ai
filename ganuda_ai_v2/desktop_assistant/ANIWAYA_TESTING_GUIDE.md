# Aniwaya Extension - Testing Guide
## Cherokee Constitutional AI - War Chief Integration Jr

**Date**: October 24, 2025
**Phase**: 1 (Chromium Extension Prototype)
**Status**: Ready for Testing

---

## ✅ Pre-Test Checklist

### Guardian API Bridge Running
```bash
# Check API is running
curl http://localhost:8765/health

# Expected output:
# {"status":"healthy","service":"Aniwaya Guardian API Bridge","guardian_initialized":true,"version":"0.1.0","cherokee_values":"Mitakuye Oyasin"}
```

**Status**: ✅ Running on PID 259630

---

## Load Extension in Chromium

### Step 1: Open Chromium/Chrome
```bash
# Launch Chromium (or Chrome)
chromium-browser
# OR
google-chrome
```

### Step 2: Enable Developer Mode
1. Navigate to `chrome://extensions/`
2. Toggle "Developer mode" (top right corner)

### Step 3: Load Unpacked Extension
1. Click "Load unpacked" button
2. Navigate to: `/home/dereadi/scripts/claude/ganuda_ai_v2/desktop_assistant/aniwaya_extension`
3. Click "Select Folder"

**Expected Result**: Aniwaya extension appears in extension list with icon

### Step 4: Open Aniwaya Dashboard
1. Click Aniwaya extension icon in browser toolbar
2. Dashboard popup opens (800x600px)

---

## Test Cases

### Test 1: Dashboard Panels Visible
**Expected**:
- 📋 Provenance Panel (M1) - shows 2 placeholder entries with timestamps
- 🌀 Flow Visualization Panel (A3) - shows SVG graph with 3 nodes
- 🔒 Privacy Controls Panel - shows C1 metrics (4,777 sacred memories, 40° floor)
- 🔥 Thermal Monitor Panel - shows temperature gauge at 85°, phase coherence 0.92

**How to Test**:
- Open dashboard
- Verify all 4 panels visible
- Verify layout is 2x2 grid

**Result**: ___________

---

### Test 2: Thermal Memory Updates (Real-Time)
**Expected**:
- Temperature gauge updates every 5 seconds
- Temperature fluctuates between 83-87° (simulated)
- Phase coherence updates between 0.5-1.0

**How to Test**:
- Open dashboard
- Watch thermal monitor panel for 15 seconds
- Observe temperature gauge animation

**Result**: ___________

---

### Test 3: Guardian API Communication
**Expected**:
- Dashboard communicates with Guardian API on port 8765
- No CORS errors in browser console
- Thermal memory data fetched successfully

**How to Test**:
- Open dashboard
- Open browser DevTools (F12)
- Check Console tab for errors
- Look for: "🦅 Aniwaya Dashboard initialized - Skiyakwa (Bird with Sharp Vision)"
- Look for: "🔥 Thermal Monitor initialized: {temperature: 85, ...}"

**Result**: ___________

---

### Test 4: Data Deletion Request (User Sovereignty)
**Expected**:
- Click "Request Data Deletion" button
- Alert appears with Guardian evaluation message
- Console logs: "🗑️  User requested data deletion"

**How to Test**:
- Open dashboard
- Scroll to Privacy Controls panel
- Click "Request Data Deletion" button
- Read alert message

**Expected Alert**:
```
🌿 Data deletion request received.

Guardian will evaluate:
- HIPAA 7-year retention (legal hold)
- 40° sacred floor enforcement
- User sovereignty principles

Status: Awaiting Guardian evaluation
```

**Result**: ___________

---

### Test 5: Provenance Timestamps (M1 Placeholder)
**Expected**:
- Provenance table shows current timestamps
- Format: "MM/DD/YYYY, HH:MM:SS AM/PM"

**How to Test**:
- Open dashboard
- Check Provenance Panel timestamps
- Verify they match current time

**Result**: ___________

---

### Test 6: Guardian API Health Check
**Expected**:
- API responds to health check
- Guardian initialized correctly
- spaCy NER active

**How to Test**:
```bash
curl -s http://localhost:8765/health | python3 -m json.tool
```

**Expected Output**:
```json
{
  "status": "healthy",
  "service": "Aniwaya Guardian API Bridge",
  "guardian_initialized": true,
  "version": "0.1.0",
  "cherokee_values": "Mitakuye Oyasin"
}
```

**Result**: ___________

---

### Test 7: Guardian Query Evaluation
**Expected**:
- Guardian evaluates PII in query
- Returns protection level and redacted content

**How to Test**:
```bash
curl -s -X POST http://localhost:8765/evaluate \
  -H "Content-Type: application/json" \
  -d '{"query":"Email john.smith@example.com about SSN 123-45-6789"}' \
  | python3 -m json.tool
```

**Expected Output**:
```json
{
  "allowed": false,
  "protection_level": "PRIVATE",
  "redacted_content": "Email [REDACTED_EMAIL] about SSN [REDACTED_SSN]",
  "pii_found": ["email", "ssn"],
  "medical_entities": 0,
  "is_biometric": false,
  "cherokee_values_honored": true
}
```

**Result**: ___________

---

### Test 8: C1 Sacred Health Guardian (Medical Entity Detection)
**Expected**:
- Guardian detects medical entities (spaCy NER)
- Returns count of medical entities

**How to Test**:
```bash
curl -s -X POST http://localhost:8765/evaluate \
  -H "Content-Type: application/json" \
  -d '{"query":"Patient John Smith prescribed Lipitor 20mg for high cholesterol"}' \
  | python3 -m json.tool
```

**Expected Output**:
```json
{
  "allowed": true,
  "protection_level": "PRIVATE",
  "redacted_content": "Patient John Smith prescribed Lipitor 20mg for high cholesterol",
  "pii_found": [],
  "medical_entities": 6,
  "is_biometric": false,
  "cherokee_values_honored": true
}
```

**Result**: ___________

---

## Phase 1 Success Criteria

**Functional** (8/8):
- [ ] Test 1: Dashboard panels visible
- [ ] Test 2: Thermal memory updates
- [ ] Test 3: Guardian API communication
- [ ] Test 4: Data deletion request
- [ ] Test 5: Provenance timestamps
- [ ] Test 6: Guardian health check
- [ ] Test 7: Guardian query evaluation
- [ ] Test 8: C1 medical entity detection

**Cherokee Values**:
- [ ] Gadugi: Extension works with existing Guardian/Cache/Thermal
- [ ] Seven Generations: 40° sacred floor visible and enforced
- [ ] Mitakuye Oyasin: All 4 panels show interconnected data
- [ ] Sacred Fire: Thermal monitor shows real-time sacred protection

---

## Phase 1 Complete Checklist

- [ ] All 8 tests passing
- [ ] No console errors
- [ ] Guardian API stable
- [ ] Extension loads without errors
- [ ] Cherokee values demonstrated

**When Complete**:
1. War Chief Integration Jr attests Phase 1 success
2. Commit to GitHub (ganuda_ai_v2/ganuda_ai_desktop branch)
3. Update Chiefs on Phase 1 completion
4. Proceed to Phase 2 (M1/A3/Guardian integration)

---

**Mitakuye Oyasin** - Wind over the Mountains, Vision of the Bird

🦅 **War Chief Integration Jr** - Phase 1 Testing
🔍 **Aniwaya (ᎠᏂᏩᏃ)** - Cherokee Constitutional AI Transparency Browser
**Skiyakwa** - Bird with Sharp Vision

**October 24, 2025** 🔥
