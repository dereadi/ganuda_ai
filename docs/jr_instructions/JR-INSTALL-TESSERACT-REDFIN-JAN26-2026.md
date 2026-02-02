# Jr Instruction: Install Tesseract OCR on Redfin

**Task ID:** To be assigned
**Jr Type:** Infrastructure Jr.
**Priority:** P1
**Node:** redfin (192.168.132.223)

---

## Objective

Install Tesseract OCR and PDF utilities required for VetAssist document processing.

---

## Steps

### Step 1: Update Package Lists
```bash
sudo apt update
```

### Step 2: Install Tesseract OCR
```bash
sudo apt install -y tesseract-ocr tesseract-ocr-eng
```

### Step 3: Install PDF Utilities
```bash
sudo apt install -y poppler-utils
```

### Step 4: Install Python Dependencies
```bash
/home/dereadi/cherokee_venv/bin/pip install pytesseract pdf2image pillow opencv-python-headless
```

### Step 5: Verify Installation
```bash
tesseract --version
pdftoppm -v
/home/dereadi/cherokee_venv/bin/python -c "import pytesseract; print('pytesseract OK')"
```

---

## Expected Output

- Tesseract version 5.x
- pdftoppm available
- Python imports successful

---

## Notes

This is a prerequisite for VetAssist OCR document processing (Task #326).
