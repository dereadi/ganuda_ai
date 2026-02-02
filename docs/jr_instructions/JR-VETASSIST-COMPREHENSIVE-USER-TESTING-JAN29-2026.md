# JR Instruction: VetAssist Comprehensive User Testing

**JR ID:** JR-VETASSIST-COMPREHENSIVE-USER-TESTING-JAN29-2026
**Priority:** P1 - Testing
**Assigned To:** Software Engineer Jr.
**Related:** ULTRATHINK-VETASSIST-DATABASE-CONFIG-DEBT-JAN29-2026

---

## Objective

Login as each of the 5 test users and populate their accounts with realistic test data including:
- Wizard sessions (claims)
- Uploaded files (medical records, service records, buddy statements)
- Research queries
- Scratchpad notes

This validates the full VetAssist user experience after the database fixes.

---

## Test Accounts

| User | Email | Password | Profile |
|------|-------|----------|---------|
| Marcus | test1@vetassist.test | password1 | Army Infantry, 70% rating, PTSD/TBI/knee/hearing |
| Sarah | test2@vetassist.test | password2 | Navy Corpsman, 40% rating, back/anxiety/tinnitus |
| David | test3@vetassist.test | password3 | Air Force Maintenance, 30% rating, shoulder/sleep apnea |
| Maria | test4@vetassist.test | password4 | Marines Motor Transport, 50% rating, MST/PTSD/migraines |
| James | test5@vetassist.test | password5 | Coast Guard, 0% rating, seeking initial claim |

---

## Step 1: Create Test Files

Create fake documents in `/ganuda/vetassist/test_uploads/`:

```bash
mkdir -p /ganuda/vetassist/test_uploads

# Medical Records
cat > /ganuda/vetassist/test_uploads/marcus_va_medical_summary.txt << 'EOF'
DEPARTMENT OF VETERANS AFFAIRS
MEDICAL RECORDS SUMMARY

Patient: Marcus Johnson
SSN: XXX-XX-1234
DOB: 1965-03-15

DIAGNOSES:
1. Post-Traumatic Stress Disorder (PTSD) - Service Connected
   - First diagnosed: 2014
   - Current severity: Moderate-Severe
   - Treatment: Weekly therapy, medication (Sertraline 100mg)

2. Traumatic Brain Injury (TBI) - Service Connected
   - Incident date: 2007 (IED blast, Iraq)
   - Symptoms: Headaches, memory issues, light sensitivity

3. Right Knee Degenerative Joint Disease
   - Related to parachute jumps during service
   - X-ray shows moderate cartilage loss

4. Bilateral Hearing Loss
   - Noise exposure during combat operations
   - Requires hearing aids

Provider: Dr. Sarah Mitchell, VA Medical Center
Date: January 2026
EOF

cat > /ganuda/vetassist/test_uploads/sarah_deployment_health_assessment.txt << 'EOF'
POST-DEPLOYMENT HEALTH ASSESSMENT
DD FORM 2796

Service Member: Sarah Williams, HM2, USN
Unit: Naval Medical Battalion 5
Deployment: Afghanistan, 2016-2017

HEALTH CONCERNS REPORTED:
- Lower back pain (onset during deployment)
- Anxiety symptoms
- Ringing in ears (tinnitus)
- Sleep difficulties

EXPOSURES:
- Burn pit smoke
- Loud noises (helicopter operations)
- High stress medical situations

Medical Provider Notes:
Service member reports chronic lower back pain that began
after carrying heavy medical equipment during patrol operations.
Recommends orthopedic evaluation and mental health screening.

Date: March 2017
EOF

cat > /ganuda/vetassist/test_uploads/david_service_treatment_records.txt << 'EOF'
SERVICE TREATMENT RECORDS EXTRACT
USAF MEDICAL GROUP

Airman: David Chen, SSgt
AFSC: 2A3X3 (Aircraft Maintenance)
Base: Travis AFB

CHRONOLOGICAL RECORD:

2012-05-14: Right shoulder strain
- Mechanism: Lifting aircraft panel
- Treatment: Ice, NSAIDs, light duty 7 days

2015-08-22: Sleep study referral
- Chief complaint: Excessive daytime sleepiness, snoring
- Diagnosis: Obstructive Sleep Apnea (moderate)
- Treatment: CPAP prescribed

2018-03-10: Dermatology consultation
- Chronic eczema, bilateral hands
- Likely related to exposure to JP-8 fuel and solvents
- Treatment: Topical steroids

2019-11-05: Shoulder MRI
- Findings: Rotator cuff partial tear, right shoulder
- Recommendation: Physical therapy, possible surgical repair
EOF

cat > /ganuda/vetassist/test_uploads/maria_buddy_statement.txt << 'EOF'
BUDDY/LAY STATEMENT
VA FORM 21-10210

I, Sergeant First Class (Ret.) Jennifer Torres, provide this statement
in support of Maria Rodriguez's VA disability claim.

I served with Maria Rodriguez in the 7th Motor Transport Battalion,
USMC, from 2012-2015. I was her direct supervisor and witnessed the
following:

1. Maria was an exemplary Marine who performed her duties with
   dedication despite increasingly difficult circumstances.

2. In early 2014, I noticed a significant change in Maria's demeanor.
   She became withdrawn, had difficulty sleeping, and sometimes had
   panic attacks during motor pool operations.

3. Maria confided in me about an incident involving a senior NCO.
   I encouraged her to report it and supported her through the
   investigation process.

4. After the incident, Maria experienced severe headaches that
   sometimes prevented her from completing her duties. Medical
   determined these were related to stress.

5. Despite these challenges, Maria completed her enlistment honorably.

I believe Maria's current conditions are directly related to her
military service. I am willing to testify to these facts.

Signed: Jennifer Torres
Date: January 15, 2026
Contact: jennifer.torres@email.com
EOF

cat > /ganuda/vetassist/test_uploads/james_separation_physical.txt << 'EOF'
SEPARATION HEALTH ASSESSMENT
DD FORM 2807-1

Service Member: James Thompson, BM2, USCG
Separation Date: July 20, 2023

CURRENT HEALTH CONCERNS:

1. Right knee pain
   - Onset: 2020, after rescue swimmer training injury
   - Current status: Chronic pain, instability
   - Impact: Difficulty with stairs, prolonged standing

2. Lower back pain
   - Onset: 2021, after heavy lifting during rescue operation
   - Current status: Daily discomfort, occasional spasms
   - Impact: Cannot lift over 30 lbs without pain

3. Depression
   - Onset: 2022, after traumatic rescue incident
   - Treatment sought during service: Yes, counseling
   - Current status: Ongoing symptoms

SERVICE MEMBER STATEMENT:
I am separating with several conditions that developed during
my 8 years of Coast Guard service. I request these conditions
be documented for potential VA disability claim.

Examining Physician: LCDR Michael Brown, MC, USCG
Date: July 2023
EOF

echo "Test files created successfully"
ls -la /ganuda/vetassist/test_uploads/
```

---

## Step 2: Login and Test Each User

For each user, perform these API calls:

### 2.1 Marcus (test1) - Already has data, verify and add more

```bash
# Login
TOKEN=$(curl -s -X POST "http://192.168.132.223:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test1@vetassist.test", "password": "password1"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Verify existing data
curl -s "http://192.168.132.223:8001/api/v1/dashboard/aa549d11-e4f5-4022-9b62-8c127b6a6213" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Update scratchpad
curl -s -X PUT "http://192.168.132.223:8001/api/v1/dashboard/aa549d11-e4f5-4022-9b62-8c127b6a6213/scratchpad" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "My VA claim notes:\n- Need to get buddy statement from Jim\n- Upload remaining medical records\n- Schedule C&P exam\n- PTSD rating currently 50%, seeking increase to 70%\n- Knee getting worse, may need surgery"}'

echo "Marcus (test1) - DONE"
```

### 2.2 Sarah (test2) - Navy Corpsman

```bash
# Login
RESPONSE=$(curl -s -X POST "http://192.168.132.223:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test2@vetassist.test", "password": "password2"}')
TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
USER_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['user']['id'])")

echo "Sarah logged in: $USER_ID"

# Start a claim wizard
curl -s -X POST "http://192.168.132.223:8001/api/v1/wizard/start" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"wizard_type": "21-526EZ", "veteran_id": "'$USER_ID'"}'

# Upload file (if upload endpoint available)
# Or note: Files can be uploaded via frontend

# Update scratchpad
curl -s -X PUT "http://192.168.132.223:8001/api/v1/dashboard/$USER_ID/scratchpad" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Claim planning:\n- Back injury from carrying medical equipment\n- Anxiety from trauma witnessed in Afghanistan\n- Tinnitus from helicopter noise exposure\n- Need deployment health assessment\n- Contact Dr. Martinez at VA for records"}'

# Submit research query
curl -s -X POST "http://192.168.132.223:8001/api/v1/research/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What evidence do I need to prove my back injury is service-connected if I was a Navy Corpsman who carried heavy medical gear?", "veteran_id": "'$USER_ID'"}'

echo "Sarah (test2) - DONE"
```

### 2.3 David (test3) - Air Force Maintenance

```bash
# Login
RESPONSE=$(curl -s -X POST "http://192.168.132.223:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test3@vetassist.test", "password": "password3"}')
TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
USER_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['user']['id'])")

echo "David logged in: $USER_ID"

# Start a claim wizard
curl -s -X POST "http://192.168.132.223:8001/api/v1/wizard/start" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"wizard_type": "21-526EZ", "veteran_id": "'$USER_ID'"}'

# Update scratchpad
curl -s -X PUT "http://192.168.132.223:8001/api/v1/dashboard/$USER_ID/scratchpad" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Claims to file:\n1. Right shoulder - rotator cuff tear from lifting aircraft panels\n2. Sleep apnea - diagnosed during service\n3. Eczema - from JP-8 fuel exposure\n\nNeed to get:\n- Buddy statement from TSgt Williams\n- Copy of sleep study results\n- Photos of eczema flare-ups"}'

# Submit research query
curl -s -X POST "http://192.168.132.223:8001/api/v1/research/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Is sleep apnea service-connected if I was diagnosed while on active duty in the Air Force?", "veteran_id": "'$USER_ID'"}'

echo "David (test3) - DONE"
```

### 2.4 Maria (test4) - Marines MST Survivor

```bash
# Login
RESPONSE=$(curl -s -X POST "http://192.168.132.223:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test4@vetassist.test", "password": "password4"}')
TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
USER_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['user']['id'])")

echo "Maria logged in: $USER_ID"

# Start a claim wizard
curl -s -X POST "http://192.168.132.223:8001/api/v1/wizard/start" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"wizard_type": "21-526EZ", "veteran_id": "'$USER_ID'"}'

# Update scratchpad
curl -s -X PUT "http://192.168.132.223:8001/api/v1/dashboard/$USER_ID/scratchpad" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "MST claim notes:\n- Have buddy statement from Sgt Torres\n- Counseling records from service\n- Current therapist letter Dr. Reyes\n- Migraines started after incident\n- Hip injury from motor transport duties\n\nVSO appointment: February 5th\nRemember: I dont have to prove the MST happened, just that my conditions are related"}'

# Submit research query
curl -s -X POST "http://192.168.132.223:8001/api/v1/research/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the special evidentiary rules for MST (Military Sexual Trauma) claims? I heard the standard of proof is different.", "veteran_id": "'$USER_ID'"}'

echo "Maria (test4) - DONE"
```

### 2.5 James (test5) - Coast Guard, Initial Claim

```bash
# Login
RESPONSE=$(curl -s -X POST "http://192.168.132.223:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test5@vetassist.test", "password": "password5"}')
TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
USER_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['user']['id'])")

echo "James logged in: $USER_ID"

# Start a claim wizard
curl -s -X POST "http://192.168.132.223:8001/api/v1/wizard/start" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"wizard_type": "21-526EZ", "veteran_id": "'$USER_ID'"}'

# Update scratchpad
curl -s -X PUT "http://192.168.132.223:8001/api/v1/dashboard/$USER_ID/scratchpad" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "First time filing - recently separated July 2023\n\nConditions to claim:\n1. Right knee - rescue swimmer training injury 2020\n2. Lower back - heavy lifting during rescue ops 2021\n3. Depression - traumatic rescue incident 2022\n\nDocuments I have:\n- Separation physical (mentions all conditions)\n- Service treatment records\n- Statement from Chief Petty Officer Davis\n\nQuestions:\n- Should I file BDD claim or regular?\n- Do I need nexus letters for everything?\n- How long does initial claim take?"}'

# Submit research queries
curl -s -X POST "http://192.168.132.223:8001/api/v1/research/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "I just separated from the Coast Guard 6 months ago. Should I file an initial VA disability claim now or wait? What is the BDD program?", "veteran_id": "'$USER_ID'"}'

curl -s -X POST "http://192.168.132.223:8001/api/v1/research/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What VA disability rating can I expect for depression related to a traumatic incident during Coast Guard service?", "veteran_id": "'$USER_ID'"}'

echo "James (test5) - DONE"
```

---

## Step 3: Verify All Data

```bash
echo "=== VERIFICATION ==="

for i in 1 2 3 4 5; do
  echo ""
  echo "--- Test User $i ---"
  RESPONSE=$(curl -s -X POST "http://192.168.132.223:8001/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"test${i}@vetassist.test\", \"password\": \"password${i}\"}")
  TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
  USER_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['user']['id'])")

  DASHBOARD=$(curl -s "http://192.168.132.223:8001/api/v1/dashboard/$USER_ID" \
    -H "Authorization: Bearer $TOKEN")

  CLAIMS=$(echo "$DASHBOARD" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('claims',[])))")
  FILES=$(echo "$DASHBOARD" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('files',[])))")
  RESEARCH=$(echo "$DASHBOARD" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('research_history',[])))")
  SCRATCHPAD=$(echo "$DASHBOARD" | python3 -c "import sys,json; d=json.load(sys.stdin); print('Yes' if d.get('scratchpad',{}).get('content') else 'No')")

  echo "  Claims: $CLAIMS"
  echo "  Files: $FILES"
  echo "  Research: $RESEARCH"
  echo "  Scratchpad: $SCRATCHPAD"
done

echo ""
echo "=== TESTING COMPLETE ==="
```

---

## Expected Results

| User | Claims | Files | Research | Scratchpad |
|------|--------|-------|----------|------------|
| Marcus (test1) | 1+ | 1+ | 6+ | Yes |
| Sarah (test2) | 1 | 0* | 1 | Yes |
| David (test3) | 1 | 0* | 1 | Yes |
| Maria (test4) | 1 | 0* | 1 | Yes |
| James (test5) | 1 | 0* | 2 | Yes |

*Files require frontend upload or direct database insert

---

## Success Criteria

1. All 5 users can login
2. All 5 users have wizard sessions started
3. All 5 users have scratchpad content
4. Research queries return results (may take time for async processing)
5. Dashboard displays all data correctly

---

FOR SEVEN GENERATIONS
