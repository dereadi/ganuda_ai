# JR Instruction: VetAssist MedGemma Integration

**Date**: January 29, 2026
**Assigned To**: AI/ML Jr
**Priority**: P1
**Estimated Effort**: 2 weeks

## Objective
Deploy MedGemma 1.5 on redfin cluster and integrate with VetAssist for medical document understanding.

## Background
MedGemma 1.5 is Google's open medical AI model released January 2026. It achieves 90% accuracy on EHR question-answering and can extract structured data from clinical notes, lab reports, and medical images.

## Prerequisites
- Access to redfin GPU cluster (192.168.132.223)
- Hugging Face account for MedGemma download
- VetAssist backend running on bluefin

## Implementation Steps

### Step 1: Download MedGemma
```bash
ssh dereadi@192.168.132.223
cd /ganuda/models
pip install huggingface_hub
huggingface-cli login
huggingface-cli download google/medgemma-1.5-27b --local-dir ./medgemma-1.5
```

### Step 2: Create Document Analysis Service
Create `/ganuda/services/medgemma/service.py`:
```python
# Service wrapper for MedGemma medical document analysis
# Accepts document text, returns structured extraction
# Integrates with existing VetAssist research queue
```

### Step 3: Define Extraction Schema
Output format for medical documents:
```json
{
  "conditions": [
    {
      "name": "string",
      "icd_code": "string",
      "diagnostic_code": "string",
      "onset_date": "string",
      "severity": "string",
      "service_connected": boolean
    }
  ],
  "providers": ["string"],
  "treatments": ["string"],
  "dates": {
    "diagnosis_date": "string",
    "treatment_dates": ["string"]
  }
}
```

### Step 4: Create API Endpoint
Add to VetAssist backend `/api/v1/ai/analyze-document`:
- POST with file_id or raw text
- Returns structured extraction
- Stores results in vetassist_pii database

### Step 5: Integration with Upload Flow
When file uploaded to VetAssist:
1. Queue analysis job in research queue
2. MedGemma service picks up job
3. Extract structured data
4. Store in document_analysis table
5. Update UI to show extracted conditions

## Verification
1. Upload sample STR (use `/ganuda/vetassist/test_uploads/david_service_treatment_records.txt`)
2. Verify extraction identifies: Right shoulder strain, Sleep Apnea, Eczema
3. Check structured output matches expected schema
4. Verify data stored correctly in database

## Security Notes
- All PII processing on goldfin VLAN
- Document content never leaves federation
- Results stored encrypted

## Resources
- MedGemma Paper: https://arxiv.org/abs/2501.xxxxx
- Hugging Face: https://huggingface.co/google/medgemma-1.5-27b
- VetAssist Backend: /ganuda/vetassist/backend/

## Deliverables
- [ ] MedGemma model deployed on redfin
- [ ] Document analysis service running
- [ ] API endpoint functional
- [ ] Integration with upload flow
- [ ] Test with all 5 sample documents
