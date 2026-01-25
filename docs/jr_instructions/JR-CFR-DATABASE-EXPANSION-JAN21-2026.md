# JR Instruction: CFR Database Expansion
## Task ID: CFR-EXPAND-001
## Priority: P1 (Council Approved - Tests Passed)
## Estimated Complexity: Medium-High

---

## Objective

Expand the `vetassist_cfr_conditions` database from 9 conditions to 800+ diagnostic codes covering all 15 body systems per 38 CFR Part 4 - Schedule for Rating Disabilities.

---

## Prerequisites

- PostgreSQL access to bluefin (zammad_production)
- Integration tests passed (18/18) - confirmed
- Council concerns resolved (Crawdad, Gecko)

---

## Reference

- Ultrathink: `/ganuda/docs/ultrathink/ULTRATHINK-CFR-DATABASE-EXPANSION-JAN21-2026.md`
- 38 CFR Part 4: https://www.ecfr.gov/current/title-38/chapter-I/part-4

---

## Implementation Steps

### Step 1: Verify Current State

```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT body_system, COUNT(*) as count
FROM vetassist_cfr_conditions
GROUP BY body_system
ORDER BY count DESC;"
```

Expected: 9 conditions across 5 body systems.

### Step 2: Add Schema Enhancements

```sql
-- Connect to bluefin
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production

-- Add helpful columns
ALTER TABLE vetassist_cfr_conditions
ADD COLUMN IF NOT EXISTS claim_frequency_rank INT,
ADD COLUMN IF NOT EXISTS last_verified TIMESTAMP DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS source_url TEXT;

-- Create index for faster synonym searches
CREATE INDEX IF NOT EXISTS idx_cfr_synonyms ON vetassist_cfr_conditions USING GIN(synonyms);
CREATE INDEX IF NOT EXISTS idx_cfr_common_names ON vetassist_cfr_conditions USING GIN(common_names);
```

### Step 3: Insert High-Priority Conditions (Top 50)

Execute the following SQL to add the most commonly claimed conditions:

```sql
-- MUSCULOSKELETAL CONDITIONS
INSERT INTO vetassist_cfr_conditions (
    diagnostic_code, condition_name, body_system, synonyms, common_names,
    rating_criteria, evidence_requirements, dbq_form, icd10_codes, description,
    claim_frequency_rank
) VALUES
-- Knee Conditions
('5256', 'Ankylosis of the Knee', 'Musculoskeletal',
 ARRAY['knee ankylosis', 'frozen knee', 'fused knee'],
 ARRAY['locked knee', 'knee won''t bend', 'stiff knee'],
 '{"30": "Favorable angle in full extension or slight flexion", "40": "In flexion between 10 and 20 degrees", "50": "In flexion between 20 and 45 degrees", "60": "Extremely unfavorable in flexion at 45 degrees or more"}'::jsonb,
 ARRAY['Current diagnosis', 'Range of motion testing', 'X-rays', 'MRI if available', 'Service connection evidence'],
 'DBQ-KNEE', ARRAY['M25.66'], 'Complete bony fixation of the knee joint', 15),

('5257', 'Knee, Other Impairment of', 'Musculoskeletal',
 ARRAY['knee instability', 'knee subluxation', 'lateral instability'],
 ARRAY['knee gives out', 'wobbly knee', 'unstable knee', 'knee buckles'],
 '{"10": "Slight recurrent subluxation or lateral instability", "20": "Moderate recurrent subluxation or lateral instability", "30": "Severe recurrent subluxation or lateral instability"}'::jsonb,
 ARRAY['Current diagnosis', 'Instability testing', 'MRI', 'Orthopedic evaluation'],
 'DBQ-KNEE', ARRAY['M23.5', 'M23.8'], 'Recurrent subluxation or lateral instability of knee', 8),

('5258', 'Cartilage, Semilunar, Dislocated', 'Musculoskeletal',
 ARRAY['meniscus tear', 'torn meniscus', 'cartilage damage knee'],
 ARRAY['torn cartilage', 'knee cartilage injury', 'meniscus injury'],
 '{"20": "With frequent episodes of locking, pain, and effusion"}'::jsonb,
 ARRAY['MRI showing tear', 'Orthopedic diagnosis', 'Surgery records if applicable'],
 'DBQ-KNEE', ARRAY['M23.2', 'S83.2'], 'Dislocated semilunar cartilage with symptoms', 12),

('5259', 'Cartilage, Semilunar, Removal of', 'Musculoskeletal',
 ARRAY['meniscectomy', 'cartilage removal', 'meniscus surgery'],
 ARRAY['knee surgery', 'cartilage removed', 'meniscus removed'],
 '{"10": "Symptomatic"}'::jsonb,
 ARRAY['Surgical records', 'Current symptoms documentation'],
 'DBQ-KNEE', ARRAY['Z96.651'], 'Removal of semilunar cartilage, symptomatic', 20),

('5260', 'Leg, Limitation of Flexion of', 'Musculoskeletal',
 ARRAY['knee flexion limitation', 'limited knee bending'],
 ARRAY['can''t bend knee', 'knee won''t bend fully', 'limited knee movement'],
 '{"0": "Flexion limited to 60 degrees", "10": "Flexion limited to 45 degrees", "20": "Flexion limited to 30 degrees", "30": "Flexion limited to 15 degrees"}'::jsonb,
 ARRAY['Range of motion testing', 'Goniometer measurements', 'X-rays'],
 'DBQ-KNEE', ARRAY['M25.56'], 'Limitation of flexion of the leg', 10),

('5261', 'Leg, Limitation of Extension of', 'Musculoskeletal',
 ARRAY['knee extension limitation', 'limited knee straightening'],
 ARRAY['can''t straighten knee', 'knee won''t straighten', 'bent knee'],
 '{"0": "Extension limited to 5 degrees", "10": "Extension limited to 10 degrees", "20": "Extension limited to 15 degrees", "30": "Extension limited to 20 degrees", "40": "Extension limited to 30 degrees", "50": "Extension limited to 45 degrees"}'::jsonb,
 ARRAY['Range of motion testing', 'Goniometer measurements', 'X-rays'],
 'DBQ-KNEE', ARRAY['M25.56'], 'Limitation of extension of the leg', 11),

-- Shoulder Conditions
('5200', 'Scapulohumeral Articulation, Ankylosis of', 'Musculoskeletal',
 ARRAY['shoulder ankylosis', 'frozen shoulder severe', 'shoulder fusion'],
 ARRAY['shoulder locked', 'can''t move shoulder', 'frozen shoulder'],
 '{"20": "Favorable, abduction to 60 degrees (minor arm)", "30": "Favorable, abduction to 60 degrees (major arm)", "30": "Intermediate (minor)", "40": "Intermediate (major)", "40": "Unfavorable (minor)", "50": "Unfavorable (major)"}'::jsonb,
 ARRAY['Orthopedic evaluation', 'Range of motion testing', 'X-rays', 'MRI'],
 'DBQ-SHOULDER', ARRAY['M24.61'], 'Ankylosis of scapulohumeral articulation', 25),

('5201', 'Arm, Limitation of Motion of', 'Musculoskeletal',
 ARRAY['shoulder ROM limitation', 'arm motion limited', 'shoulder mobility reduced'],
 ARRAY['can''t raise arm', 'shoulder pain lifting', 'limited arm movement'],
 '{"20": "At shoulder level (both arms)", "20": "Midway between side and shoulder (minor)", "30": "Midway between side and shoulder (major)", "30": "To 25 degrees from side (minor)", "40": "To 25 degrees from side (major)"}'::jsonb,
 ARRAY['Range of motion testing', 'Orthopedic evaluation', 'X-rays'],
 'DBQ-SHOULDER', ARRAY['M25.51'], 'Limitation of motion of arm', 9),

('5202', 'Humerus, Other Impairment of', 'Musculoskeletal',
 ARRAY['shoulder impingement', 'rotator cuff', 'humerus injury'],
 ARRAY['shoulder injury', 'rotator cuff tear', 'shoulder problems'],
 '{"20": "Malunion with moderate deformity (both)", "20": "Recurrent dislocation at scapulohumeral joint, infrequent (minor)", "30": "Malunion with marked deformity (major)", "30": "Recurrent dislocation, frequent (minor)", "40": "Recurrent dislocation, frequent (major)"}'::jsonb,
 ARRAY['X-rays', 'MRI', 'Orthopedic evaluation', 'Surgery records if applicable'],
 'DBQ-SHOULDER', ARRAY['S42.2', 'M75.1'], 'Other impairment of humerus', 14),

('5203', 'Clavicle or Scapula, Impairment of', 'Musculoskeletal',
 ARRAY['clavicle fracture', 'collarbone injury', 'scapula injury'],
 ARRAY['broken collarbone', 'shoulder blade injury', 'collarbone pain'],
 '{"10": "Malunion or nonunion without loose movement", "20": "Nonunion with loose movement or dislocation"}'::jsonb,
 ARRAY['X-rays', 'Orthopedic evaluation', 'Surgery records'],
 'DBQ-SHOULDER', ARRAY['S42.0', 'S42.1'], 'Impairment of clavicle or scapula', 22),

-- Hip Conditions
('5250', 'Hip, Ankylosis of', 'Musculoskeletal',
 ARRAY['hip ankylosis', 'fused hip', 'hip fusion'],
 ARRAY['hip locked', 'can''t move hip', 'frozen hip'],
 '{"60": "Favorable, in flexion at 20-40 degrees", "70": "Intermediate", "90": "Unfavorable, extremely unfavorable ankylosis"}'::jsonb,
 ARRAY['X-rays', 'Orthopedic evaluation', 'Range of motion testing'],
 'DBQ-HIP', ARRAY['M24.65'], 'Ankylosis of hip', 30),

('5251', 'Thigh, Limitation of Extension of', 'Musculoskeletal',
 ARRAY['hip extension limited', 'thigh extension limited'],
 ARRAY['can''t extend leg', 'hip won''t straighten'],
 '{"10": "Extension limited to 5 degrees"}'::jsonb,
 ARRAY['Range of motion testing', 'Orthopedic evaluation'],
 'DBQ-HIP', ARRAY['M25.55'], 'Limitation of extension of thigh', 35),

('5252', 'Thigh, Limitation of Flexion of', 'Musculoskeletal',
 ARRAY['hip flexion limited', 'thigh flexion limited'],
 ARRAY['can''t bend at hip', 'hip won''t flex', 'trouble sitting'],
 '{"10": "Flexion limited to 45 degrees", "20": "Flexion limited to 30 degrees", "30": "Flexion limited to 20 degrees", "40": "Flexion limited to 10 degrees"}'::jsonb,
 ARRAY['Range of motion testing', 'Orthopedic evaluation'],
 'DBQ-HIP', ARRAY['M25.55'], 'Limitation of flexion of thigh', 18),

-- Ankle Conditions
('5270', 'Ankle, Ankylosis of', 'Musculoskeletal',
 ARRAY['ankle ankylosis', 'fused ankle', 'frozen ankle'],
 ARRAY['ankle locked', 'can''t move ankle'],
 '{"20": "In plantar flexion less than 30 degrees", "30": "In plantar flexion between 30 and 40 degrees or in dorsiflexion between 0 and 10 degrees", "40": "In plantar flexion at more than 40 degrees or dorsiflexion at more than 10 degrees"}'::jsonb,
 ARRAY['X-rays', 'Orthopedic evaluation', 'Range of motion testing'],
 'DBQ-ANKLE', ARRAY['M24.67'], 'Ankylosis of ankle', 28),

('5271', 'Ankle, Limited Motion of', 'Musculoskeletal',
 ARRAY['ankle ROM limited', 'ankle motion restricted'],
 ARRAY['stiff ankle', 'ankle won''t move', 'limited ankle movement'],
 '{"10": "Moderate limitation of motion", "20": "Marked limitation of motion"}'::jsonb,
 ARRAY['Range of motion testing', 'Orthopedic evaluation'],
 'DBQ-ANKLE', ARRAY['M25.57'], 'Limited motion of ankle', 16),

-- MENTAL HEALTH CONDITIONS
('9434', 'Major Depressive Disorder', 'Mental Disorders',
 ARRAY['depression', 'MDD', 'clinical depression', 'major depression'],
 ARRAY['depression', 'depressed', 'sad all the time', 'can''t get out of bed'],
 '{"0": "Diagnosed but symptoms controlled by medication", "10": "Mild or transient symptoms", "30": "Occasional decrease in work efficiency", "50": "Reduced reliability and productivity", "70": "Deficiencies in most areas", "100": "Total occupational and social impairment"}'::jsonb,
 ARRAY['Mental health diagnosis', 'Treatment records', 'Medication history', 'Psychotherapy records', 'Buddy statements'],
 'DBQ-MENTAL-DISORDERS', ARRAY['F32', 'F33'], 'Major depressive disorder', 5),

('9413', 'Generalized Anxiety Disorder', 'Mental Disorders',
 ARRAY['anxiety', 'GAD', 'anxiety disorder', 'chronic anxiety'],
 ARRAY['anxiety', 'anxious', 'worried all the time', 'panic', 'nervous'],
 '{"0": "Diagnosed but symptoms controlled", "10": "Mild or transient symptoms", "30": "Occasional decrease in work efficiency", "50": "Reduced reliability and productivity", "70": "Deficiencies in most areas", "100": "Total occupational and social impairment"}'::jsonb,
 ARRAY['Mental health diagnosis', 'Treatment records', 'Medication history'],
 'DBQ-MENTAL-DISORDERS', ARRAY['F41.1'], 'Generalized anxiety disorder', 6),

('9440', 'Chronic Adjustment Disorder', 'Mental Disorders',
 ARRAY['adjustment disorder', 'situational depression'],
 ARRAY['trouble adjusting', 'stress reaction', 'adjustment problems'],
 '{"0": "Diagnosed but controlled", "10": "Mild symptoms", "30": "Occasional decrease in work efficiency", "50": "Reduced reliability", "70": "Deficiencies in most areas", "100": "Total impairment"}'::jsonb,
 ARRAY['Mental health diagnosis', 'Treatment records', 'Stressor documentation'],
 'DBQ-MENTAL-DISORDERS', ARRAY['F43.2'], 'Chronic adjustment disorder', 21),

-- CARDIOVASCULAR CONDITIONS
('7000', 'Valvular Heart Disease', 'Cardiovascular',
 ARRAY['heart valve disease', 'valvular disease', 'heart murmur'],
 ARRAY['heart valve problem', 'leaky valve', 'heart murmur'],
 '{"10": "Workload of 7-10 METs results in dyspnea", "30": "Workload of 5-7 METs results in dyspnea", "60": "More than one episode of acute congestive heart failure per year", "100": "Chronic congestive heart failure"}'::jsonb,
 ARRAY['Echocardiogram', 'Cardiac evaluation', 'Exercise stress test', 'Treatment records'],
 'DBQ-HEART', ARRAY['I05', 'I06', 'I07', 'I08'], 'Valvular heart disease including rheumatic', 40),

('7005', 'Arteriosclerotic Heart Disease (CAD)', 'Cardiovascular',
 ARRAY['coronary artery disease', 'CAD', 'heart disease', 'arteriosclerosis'],
 ARRAY['heart disease', 'blocked arteries', 'heart attack history', 'coronary disease'],
 '{"10": "Workload of 7-10 METs results in dyspnea", "30": "Workload of 5-7 METs results in dyspnea", "60": "More than one episode of acute CHF per year or workload 3-5 METs", "100": "Chronic CHF or workload 3 METs or less"}'::jsonb,
 ARRAY['Cardiac catheterization', 'Stress test', 'Echocardiogram', 'Cardiology evaluation'],
 'DBQ-HEART', ARRAY['I25.1', 'I25.10'], 'Coronary artery disease', 19),

('7101', 'Hypertensive Vascular Disease (Hypertension)', 'Cardiovascular',
 ARRAY['hypertension', 'high blood pressure', 'HTN'],
 ARRAY['high blood pressure', 'BP problems', 'hypertension'],
 '{"10": "Diastolic predominantly 100 or more, or systolic predominantly 160 or more, or history of diastolic 100 or more requiring continuous medication", "20": "Diastolic predominantly 110 or more, or systolic predominantly 200 or more", "40": "Diastolic predominantly 120 or more", "60": "Diastolic predominantly 130 or more"}'::jsonb,
 ARRAY['Blood pressure readings', 'Medication records', 'Cardiology evaluation'],
 'DBQ-HYPERTENSION', ARRAY['I10', 'I11', 'I12', 'I13'], 'Hypertensive vascular disease', 7),

-- RESPIRATORY CONDITIONS
('6602', 'Bronchial Asthma', 'Respiratory',
 ARRAY['asthma', 'reactive airway disease', 'bronchial asthma'],
 ARRAY['asthma', 'trouble breathing', 'wheezing', 'asthma attacks'],
 '{"10": "FEV-1 of 71-80% predicted, or FEV-1/FVC of 71-80%, or intermittent inhalational therapy", "30": "FEV-1 of 56-70% predicted, or FEV-1/FVC of 56-70%, or daily inhalational therapy", "60": "FEV-1 of 40-55% predicted, or FEV-1/FVC of 40-55%, or at least monthly visits for exacerbations", "100": "FEV-1 less than 40% predicted, or more than one attack per week with episodes of respiratory failure"}'::jsonb,
 ARRAY['Pulmonary function tests (PFT)', 'Treatment records', 'Medication history', 'Hospitalization records'],
 'DBQ-RESPIRATORY', ARRAY['J45'], 'Bronchial asthma', 17),

('6604', 'Chronic Obstructive Pulmonary Disease (COPD)', 'Respiratory',
 ARRAY['COPD', 'chronic bronchitis', 'emphysema'],
 ARRAY['COPD', 'emphysema', 'chronic lung disease', 'trouble breathing'],
 '{"10": "FEV-1 of 71-80% predicted, or FEV-1/FVC of 71-80%, or DLCO of 66-80% predicted", "30": "FEV-1 of 56-70% predicted, or FEV-1/FVC of 56-70%, or DLCO of 56-65% predicted", "60": "FEV-1 of 40-55% predicted, or FEV-1/FVC of 40-55%, or DLCO of 40-55% predicted", "100": "FEV-1 less than 40% predicted, or FEV-1/FVC less than 40%, or DLCO less than 40% predicted, or maximum exercise capacity less than 15 ml/kg/min oxygen consumption"}'::jsonb,
 ARRAY['Pulmonary function tests', 'Chest X-ray or CT', 'Treatment records', 'Oxygen requirement documentation'],
 'DBQ-RESPIRATORY', ARRAY['J44', 'J43'], 'Chronic obstructive pulmonary disease', 13),

-- DIGESTIVE CONDITIONS
('7301', 'Peritoneal Adhesions', 'Digestive',
 ARRAY['abdominal adhesions', 'intestinal adhesions', 'post-surgical adhesions'],
 ARRAY['stomach adhesions', 'abdominal scarring', 'bowel adhesions'],
 '{"0": "Mild, pulling pain on attempting work or aggravated by movements of body", "10": "Moderate, pulling pain on attempting work or aggravated by movements", "30": "Moderately severe, partial obstruction manifested by delayed motility", "50": "Severe, definite partial obstruction with frequent and prolonged episodes of severe colic distension"}'::jsonb,
 ARRAY['Surgical records', 'Imaging studies', 'GI evaluation'],
 'DBQ-INTESTINES', ARRAY['K66.0'], 'Peritoneal adhesions', 38),

('7305', 'Duodenal Ulcer', 'Digestive',
 ARRAY['peptic ulcer', 'stomach ulcer', 'gastric ulcer'],
 ARRAY['ulcer', 'stomach ulcer', 'ulcer pain'],
 '{"10": "Mild, recurring symptoms once or twice yearly", "20": "Moderate, recurring episodes of severe symptoms 2-3 times per year", "40": "Moderately severe, less than continuous but with impairment of health", "60": "Severe, pain partially relieved by standard therapy, periodic vomiting, recurrent hematemesis or melena"}'::jsonb,
 ARRAY['Endoscopy', 'GI evaluation', 'Treatment records', 'H. pylori testing'],
 'DBQ-STOMACH', ARRAY['K26'], 'Duodenal ulcer', 32),

('7319', 'Irritable Colon Syndrome (IBS)', 'Digestive',
 ARRAY['IBS', 'irritable bowel syndrome', 'spastic colon'],
 ARRAY['IBS', 'irritable bowel', 'stomach problems', 'bowel issues'],
 '{"0": "Mild, disturbances of bowel function with occasional episodes of abdominal distress", "10": "Moderate, frequent episodes of bowel disturbance with abdominal distress", "30": "Severe, diarrhea or alternating diarrhea and constipation, with more or less constant abdominal distress"}'::jsonb,
 ARRAY['GI evaluation', 'Colonoscopy if done', 'Treatment records', 'Food diary if available'],
 'DBQ-INTESTINES', ARRAY['K58'], 'Irritable colon syndrome', 23),

('7338', 'Hernia, Inguinal', 'Digestive',
 ARRAY['inguinal hernia', 'groin hernia'],
 ARRAY['hernia', 'groin bulge', 'inguinal hernia'],
 '{"0": "Not operated, but remediable", "10": "Postoperative recurrent, readily reducible, well supported by truss or belt", "30": "Small, postoperative recurrent, or unoperated irremediable", "60": "Large, postoperative, recurrent, not well supported, not readily reducible"}'::jsonb,
 ARRAY['Physical examination', 'Surgical records', 'Imaging if available'],
 'DBQ-HERNIAS', ARRAY['K40'], 'Inguinal hernia', 27),

-- GENITOURINARY CONDITIONS
('7517', 'Bladder, Injury of', 'Genitourinary',
 ARRAY['bladder injury', 'bladder trauma', 'neurogenic bladder'],
 ARRAY['bladder problems', 'urinary issues', 'incontinence'],
 '{"20": "Requiring the wearing of absorbent materials which must be changed less than 2 times per day", "40": "Requiring the wearing of absorbent materials which must be changed 2 to 4 times per day", "60": "Requiring the use of an appliance or the wearing of absorbent materials which must be changed more than 4 times per day"}'::jsonb,
 ARRAY['Urology evaluation', 'Urodynamic testing', 'Treatment records'],
 'DBQ-GENITOURINARY', ARRAY['S37.2'], 'Injury of bladder', 36),

('7522', 'Penis, Deformity, with Loss of Erectile Power', 'Genitourinary',
 ARRAY['erectile dysfunction', 'ED', 'impotence'],
 ARRAY['ED', 'erectile dysfunction', 'impotence', 'sexual dysfunction'],
 '{"20": "Deformity with loss of erectile power"}'::jsonb,
 ARRAY['Urology evaluation', 'Treatment records', 'Medication history'],
 'DBQ-MALE-REPRODUCTIVE', ARRAY['N52'], 'Deformity of penis with loss of erectile power', 24),

-- SKIN CONDITIONS
('7806', 'Dermatitis or Eczema', 'Skin',
 ARRAY['eczema', 'dermatitis', 'atopic dermatitis', 'contact dermatitis'],
 ARRAY['skin rash', 'eczema', 'itchy skin', 'skin condition'],
 '{"0": "Less than 5% of entire body or exposed areas affected, no more than topical therapy required", "10": "At least 5% but less than 20% of entire body or exposed areas affected, or intermittent systemic therapy required", "30": "20-40% of entire body or exposed areas affected, or systemic therapy required for 6 weeks or more", "60": "More than 40% of entire body or exposed areas affected, or constant/near-constant systemic therapy required"}'::jsonb,
 ARRAY['Dermatology evaluation', 'Photographs', 'Treatment records', 'Medication history'],
 'DBQ-SKIN', ARRAY['L20', 'L23', 'L24', 'L25', 'L30'], 'Dermatitis or eczema', 26),

('7816', 'Psoriasis', 'Skin',
 ARRAY['psoriasis', 'plaque psoriasis', 'psoriatic arthritis'],
 ARRAY['psoriasis', 'scaly skin', 'skin patches'],
 '{"0": "Less than 5% of body affected", "10": "At least 5% but less than 20% of body affected", "30": "20-40% of body affected or systemic therapy required", "60": "More than 40% of body affected or constant systemic therapy required"}'::jsonb,
 ARRAY['Dermatology evaluation', 'Photographs', 'Treatment records'],
 'DBQ-SKIN', ARRAY['L40'], 'Psoriasis', 33),

('7817', 'Malignant Skin Neoplasms (Skin Cancer)', 'Skin',
 ARRAY['skin cancer', 'melanoma', 'basal cell carcinoma', 'squamous cell carcinoma'],
 ARRAY['skin cancer', 'melanoma', 'cancer on skin'],
 '{"0": "If there has been no local recurrence or metastasis, rate on residuals", "100": "During treatment, then rated on residuals"}'::jsonb,
 ARRAY['Pathology reports', 'Oncology records', 'Surgery records', 'Treatment records'],
 'DBQ-SKIN', ARRAY['C43', 'C44'], 'Malignant skin neoplasms', 34),

-- NEUROLOGICAL (additional)
('8515', 'Paralysis of the Median Nerve', 'Neurological',
 ARRAY['carpal tunnel syndrome', 'CTS', 'median nerve damage'],
 ARRAY['carpal tunnel', 'wrist pain', 'hand numbness', 'tingling in hand'],
 '{"10": "Mild incomplete paralysis (both hands)", "30": "Moderate incomplete paralysis (major hand)", "20": "Moderate incomplete paralysis (minor hand)", "50": "Severe incomplete paralysis (major)", "40": "Severe incomplete paralysis (minor)", "70": "Complete paralysis (major)", "60": "Complete paralysis (minor)"}'::jsonb,
 ARRAY['EMG/NCV testing', 'Neurology evaluation', 'Surgery records if applicable'],
 'DBQ-PERIPHERAL-NERVES', ARRAY['G56.0'], 'Paralysis of median nerve (carpal tunnel)', 4),

('8520', 'Paralysis of the Sciatic Nerve', 'Neurological',
 ARRAY['sciatica', 'sciatic nerve damage', 'radiculopathy'],
 ARRAY['sciatica', 'leg pain', 'shooting pain down leg', 'sciatic pain'],
 '{"10": "Mild incomplete paralysis", "20": "Moderate incomplete paralysis", "40": "Moderately severe incomplete paralysis", "60": "Severe incomplete paralysis with marked muscular atrophy", "80": "Complete paralysis, foot dangles and drops"}'::jsonb,
 ARRAY['EMG/NCV testing', 'MRI of spine', 'Neurology evaluation'],
 'DBQ-PERIPHERAL-NERVES', ARRAY['G57.0', 'M54.3'], 'Paralysis of sciatic nerve (sciatica)', 3),

('8521', 'Paralysis of the External Popliteal (Common Peroneal) Nerve', 'Neurological',
 ARRAY['foot drop', 'peroneal nerve palsy', 'common peroneal nerve damage'],
 ARRAY['foot drop', 'can''t lift foot', 'tripping'],
 '{"10": "Mild incomplete paralysis", "20": "Moderate incomplete paralysis", "30": "Severe incomplete paralysis", "40": "Complete paralysis with foot drop"}'::jsonb,
 ARRAY['EMG/NCV testing', 'Neurology evaluation', 'Gait analysis'],
 'DBQ-PERIPHERAL-NERVES', ARRAY['G57.3'], 'Paralysis of external popliteal nerve (foot drop)', 29),

-- ENDOCRINE CONDITIONS
('7903', 'Hypothyroidism', 'Endocrine',
 ARRAY['underactive thyroid', 'low thyroid', 'thyroid deficiency'],
 ARRAY['thyroid problems', 'underactive thyroid', 'hypothyroid'],
 '{"10": "Fatigability, or continuous medication required for control", "30": "Fatigability, constipation, and mental sluggishness", "60": "Muscular weakness, mental disturbance, and weight gain", "100": "Cold intolerance, muscular weakness, cardiovascular involvement, mental disturbance, bradycardia, and sleepiness including narcolepsy"}'::jsonb,
 ARRAY['Thyroid function tests (TSH, T4)', 'Endocrinology evaluation', 'Medication records'],
 'DBQ-ENDOCRINE', ARRAY['E03'], 'Hypothyroidism', 31),

('7913', 'Diabetes Mellitus', 'Endocrine',
 ARRAY['diabetes', 'type 2 diabetes', 'type 1 diabetes', 'DM'],
 ARRAY['diabetes', 'sugar diabetes', 'diabetic'],
 '{"10": "Manageable by restricted diet only", "20": "Requiring insulin and restricted diet, or oral hypoglycemic agent and restricted diet", "40": "Requiring insulin, restricted diet, and regulation of activities", "60": "Requiring insulin, restricted diet, and regulation of activities with episodes of ketoacidosis or hypoglycemic reactions", "100": "Requiring more than one daily injection of insulin, restricted diet, and regulation of activities with episodes of ketoacidosis or hypoglycemic reactions requiring at least 3 hospitalizations per year or weekly visits to diabetic care provider"}'::jsonb,
 ARRAY['HbA1c levels', 'Blood glucose logs', 'Endocrinology records', 'Medication history', 'Complications documentation'],
 'DBQ-ENDOCRINE', ARRAY['E11', 'E10'], 'Diabetes mellitus', 2),

-- EYE CONDITIONS
('6027', 'Cataract', 'Eye',
 ARRAY['cataracts', 'lens opacity', 'cloudy lens'],
 ARRAY['cataracts', 'cloudy vision', 'blurry vision'],
 '{"Based on visual impairment": "Rate based on resulting visual impairment"}'::jsonb,
 ARRAY['Ophthalmology evaluation', 'Visual acuity testing', 'Surgery records if applicable'],
 'DBQ-EYE', ARRAY['H25', 'H26'], 'Cataract of any type', 37),

('6066', 'Visual Impairment', 'Eye',
 ARRAY['vision loss', 'visual acuity loss', 'blindness'],
 ARRAY['vision problems', 'can''t see well', 'poor vision', 'blind'],
 '{"0": "Vision correctable to 20/40 in both eyes", "10": "Vision 20/50 in one eye, 20/40 in other", "20": "Vision 20/70 in one eye, 20/50 in other", "30": "Vision 20/100 in both eyes", "40": "Vision 20/200 in one eye, 20/100 in other", "50": "Vision 20/200 in both eyes", "60": "Vision 10/200 in both eyes", "70": "Vision 5/200 in both eyes", "80": "Light perception only in both eyes", "90": "Light perception only in one eye, no light perception in other", "100": "No light perception in both eyes"}'::jsonb,
 ARRAY['Visual acuity testing', 'Visual field testing', 'Ophthalmology evaluation'],
 'DBQ-EYE', ARRAY['H54'], 'Visual impairment based on visual acuity', 39)

ON CONFLICT (diagnostic_code) DO UPDATE SET
    condition_name = EXCLUDED.condition_name,
    body_system = EXCLUDED.body_system,
    synonyms = EXCLUDED.synonyms,
    common_names = EXCLUDED.common_names,
    rating_criteria = EXCLUDED.rating_criteria,
    evidence_requirements = EXCLUDED.evidence_requirements,
    dbq_form = EXCLUDED.dbq_form,
    icd10_codes = EXCLUDED.icd10_codes,
    description = EXCLUDED.description,
    claim_frequency_rank = EXCLUDED.claim_frequency_rank,
    last_verified = NOW();
```

### Step 4: Verify Expansion

```sql
-- Count total conditions
SELECT COUNT(*) as total_conditions FROM vetassist_cfr_conditions;

-- Count by body system
SELECT body_system, COUNT(*) as count
FROM vetassist_cfr_conditions
GROUP BY body_system
ORDER BY count DESC;

-- Verify top conditions have synonyms
SELECT diagnostic_code, condition_name, array_length(synonyms, 1) as synonym_count
FROM vetassist_cfr_conditions
WHERE claim_frequency_rank IS NOT NULL
ORDER BY claim_frequency_rank
LIMIT 20;
```

### Step 5: Test Search Functionality

```bash
# Test various search terms
curl -s -X POST http://localhost:8001/api/v1/conditions/map \
  -H "Content-Type: application/json" \
  -d '{"description": "knee pain"}' | python3 -m json.tool

curl -s -X POST http://localhost:8001/api/v1/conditions/map \
  -H "Content-Type: application/json" \
  -d '{"description": "diabetes"}' | python3 -m json.tool

curl -s -X POST http://localhost:8001/api/v1/conditions/map \
  -H "Content-Type: application/json" \
  -d '{"description": "carpal tunnel"}' | python3 -m json.tool
```

---

## Acceptance Criteria

1. Database contains 40+ conditions (initial expansion)
2. All 15 body systems represented
3. Top 20 conditions have comprehensive synonyms
4. Rating criteria present for all conditions
5. Search returns relevant results for common terms

---

## Future Expansion

After this initial batch, continue adding conditions:
- Remaining musculoskeletal codes (5000-5299)
- Complete mental health section (9200-9499)
- Full respiratory section (6500-6899)
- Infectious diseases (9900-9999)

Target: 800+ total conditions

---

## Security Notes

- Do not include any PII in the database
- All data sourced from public 38 CFR
- Rating criteria is publicly available information

---

*Cherokee AI Federation - For Seven Generations*
*Sprint 3 Integration Tests: 18/18 PASSED*
*Council Vote Reference: 1092bfcd53726375*
