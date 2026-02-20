# Jr Instruction: PyPDFForm Part 1 — Install Library & Download Templates

**ID:** JR-VETASSIST-PYPDF-PART1-INSTALL-FEB06-2026
**Priority:** P0
**Part:** 1 of 4

---

## Objective

Install PyPDFForm library and download VA form templates.

---

## Step 1: Install PyPDFForm

```bash
/ganuda/vetassist/backend/venv/bin/pip install pypdfform
```

---

## Step 2: Create templates directory

```bash
mkdir -p /ganuda/vetassist/templates/va_forms
```

---

## Step 3: Download VA Form 21-526EZ

```bash
curl -L -o /ganuda/vetassist/templates/va_forms/21-526EZ.pdf "https://www.vba.va.gov/pubs/forms/VBA-21-526EZ-ARE.pdf"
```

---

## Step 4: Download VA Form 21-0781

```bash
curl -L -o /ganuda/vetassist/templates/va_forms/21-0781.pdf "https://www.vba.va.gov/pubs/forms/VBA-21-0781-ARE.pdf"
```

---

## Step 5: Download VA Form 21-0781a

```bash
curl -L -o /ganuda/vetassist/templates/va_forms/21-0781a.pdf "https://www.vba.va.gov/pubs/forms/VBA-21-0781a-ARE.pdf"
```

---

## Step 6: Verify installation

```bash
ls -la /ganuda/vetassist/templates/va_forms/
```

---

*Part 1 of 4*
