# JR INSTRUCTION: POC - Evaluate Electronic CFR for RAG Pipeline

**Task ID:** ASSIST-POC-ECFR
**Priority:** P2 - Proof of concept
**Assigned To:** Any available Jr
**Created By:** TPM + Council (APPROVE pending POC)
**Date:** 2026-02-04
**Estimated Effort:** 6-8 hours
**Node:** Any (requires git, Python 3.11+)

---

## Objective

Evaluate the AlextheYounga/ecfr GitHub repository as a data source for our RAG pipeline across VetAssist, SSIDAssist, and TribeAssist applications.

## Context

Our current RAG pipeline uses:
- 38 CFR (Veterans' Benefits) for VetAssist
- 20 CFR Parts 404/416 (SSDI/SSI) for SSIDAssist
- 25 CFR Part 70 (CDIB) for TribeAssist

We manually scrape and chunk these regulations. If the ecfr repository provides clean, current, and accurate CFR data, we could automate ingestion and updates.

## Success Criteria

- Data accuracy confirmed (5+ random section comparisons)
- Data format suitable for RAG chunking
- Update mechanism identified and documented
- Security audit completed (no executable risks)
- Clear recommendation: USE ECFR REPO, USE GPO, USE OFFICIAL API, or BUILD SCRAPER

---

## Steps

### 1. Clone and Inspect Repository

```bash
# Create test directory
mkdir -p /ganuda/tmp/ecfr-poc
cd /ganuda/tmp/ecfr-poc

# Clone repository
git clone https://github.com/AlextheYounga/ecfr.git
cd ecfr

# Inspect structure
tree -L 3 -h
ls -lh

# Check for executable code
find . -type f -name "*.py" -o -name "*.js" -o -name "*.sh" -o -name "*.exe"

# Examine README and documentation
cat README.md
```

**Verification:** Repository cloned, structure understood

### 2. Extract Target Titles

Locate and extract these specific CFR titles:

```bash
# Title 38 - Veterans' Benefits (VetAssist)
find . -path "*title-38*" -type f

# Title 20 Part 404 - SSDI (SSIDAssist)
find . -path "*title-20*" -path "*part-404*" -type f

# Title 20 Part 416 - SSI (SSIDAssist)
find . -path "*title-20*" -path "*part-416*" -type f

# Title 25 Part 70 - CDIB (TribeAssist)
find . -path "*title-25*" -path "*part-70*" -type f
```

Copy extracted data to organized structure:

```bash
mkdir -p /ganuda/tmp/ecfr-poc/extracted/{title-38,title-20-404,title-20-416,title-25-70}

# Copy relevant files
# [Adjust paths based on actual repo structure]
```

**Verification:** All four target datasets extracted

### 3. Data Quality Assessment

#### 3.1 Accuracy Check

Compare 5 random sections against official eCFR.gov:

```python
# Create accuracy_test.py
import random
import requests
from bs4 import BeautifulSoup

sections_to_test = [
    ("38", "4", "17a"),  # 38 CFR 4.17a - Mental disorders rating table
    ("20", "404", "1501"),  # 20 CFR 404.1501 - Disability determination
    ("20", "416", "920"),  # 20 CFR 416.920 - Sequential evaluation
    ("25", "70", "4"),  # 25 CFR 70.4 - CDIB application
    ("38", "3", "102"),  # 38 CFR 3.102 - Reasonable doubt
]

def fetch_official_cfr(title, part, section):
    """Fetch section text from official eCFR.gov"""
    url = f"https://www.ecfr.gov/current/title-{title}/part-{part}/section-{part}.{section}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Extract section text
    content = soup.find('div', {'class': 'content-block'})
    return content.get_text(strip=True) if content else None

def compare_with_repo(title, part, section):
    """Compare repo version with official version"""
    # Load from repo
    repo_path = f"extracted/title-{title}/part-{part}/section-{section}.txt"  # Adjust as needed

    with open(repo_path, 'r') as f:
        repo_text = f.read()

    # Fetch official
    official_text = fetch_official_cfr(title, part, section)

    # Compare (simple character difference for POC)
    if repo_text.strip() == official_text.strip():
        return "EXACT_MATCH"
    else:
        # Calculate similarity
        from difflib import SequenceMatcher
        ratio = SequenceMatcher(None, repo_text, official_text).ratio()
        return f"SIMILARITY: {ratio:.2%}"

# Run comparison
for title, part, section in sections_to_test:
    result = compare_with_repo(title, part, section)
    print(f"{title} CFR {part}.{section}: {result}")
```

**Verification:** At least 4 out of 5 sections match official eCFR.gov text with >95% similarity

#### 3.2 Currency Check

```bash
# Check last commit date
git log -1 --format="%ai %s" -- title-38/
git log -1 --format="%ai %s" -- title-20/
git log -1 --format="%ai %s" -- title-25/

# Check for update date metadata in files
grep -r "effective.*date" title-38/ | head -5
grep -r "last.*updated" title-20/ | head -5
```

Compare against official eCFR update dates:
- https://www.ecfr.gov/current/title-38 (check "Current through" date)
- https://www.ecfr.gov/current/title-20 (check "Current through" date)
- https://www.ecfr.gov/current/title-25 (check "Current through" date)

**Evaluation Criteria:**
- Data is current within 30 days: EXCELLENT
- Data is current within 90 days: ACCEPTABLE
- Data is >90 days old: UNACCEPTABLE

**Verification:** Currency assessment documented

#### 3.3 Cross-Reference Integrity

Test if cross-references are preserved:

```bash
# Search for cross-reference patterns
grep -n "See.*§" title-38/ | head -10
grep -n "See.*CFR" title-20/ | head -10
grep -n "paragraph.*(.*)" title-25/ | head -10
```

Example test cases:
- 38 CFR 4.130 (Mental disorders) references 4.132 (Rating schedule)
- 20 CFR 404.1520 references 404.1560 (Work capacity)
- Cross-references should be hyperlinked or at least preserved as text

**Verification:** Cross-references are intact and identifiable

#### 3.4 Table and Chart Integrity

```bash
# Look for table data
grep -r "TABLE\|Table" title-38/ | head -5
grep -r "Column\|Row" title-20/ | head -5

# Check for structured data
find . -name "*.csv" -o -name "*.json" -o -name "*.xml"
```

Test cases:
- 38 CFR 4.71a (Schedule of ratings - musculoskeletal) contains tables
- 20 CFR 404.1046 (Quarter of coverage) contains dollar amounts table

**Verification:** Tables are present and machine-readable

### 4. RAG Suitability Assessment

#### 4.1 Data Format Analysis

```bash
# Identify file formats
find extracted/ -type f -exec file {} \; | sort | uniq -c

# Examine sample files
head -100 extracted/title-38/[first-section-file]
head -100 extracted/title-20-404/[first-section-file]
```

Document format characteristics:
- File extension: .txt, .xml, .json, .md?
- Encoding: UTF-8, ASCII?
- Structure: Plain text, XML with tags, JSON with fields?
- Metadata: Section numbers, titles, effective dates?

**Verification:** Format documented with examples

#### 4.2 Chunking Strategy

Design chunking approach for RAG:

```python
# Create chunking_test.py

def chunk_by_section(cfr_file):
    """
    Chunk CFR data by section for semantic retrieval.

    Strategy:
    - Each section (e.g., §404.1520) is one chunk
    - Include section number, title, and full text
    - Preserve subsection hierarchy (a), (b), (1), (2)
    - Max chunk size: 1000 tokens (~750 words)
    """
    chunks = []

    # Parse file (adjust based on actual format)
    with open(cfr_file, 'r') as f:
        content = f.read()

    # Split by section markers
    # Example: "§ 404.1520" or "Section 404.1520"
    sections = re.split(r'§\s*\d+\.\d+', content)

    for section in sections:
        if len(section.strip()) == 0:
            continue

        # Extract metadata
        section_num = extract_section_number(section)
        section_title = extract_section_title(section)

        # Create chunk
        chunk = {
            "section": section_num,
            "title": section_title,
            "text": section.strip(),
            "source": f"20 CFR {section_num}",
            "type": "regulation"
        }

        chunks.append(chunk)

    return chunks

# Test on 10 sections
test_chunks = chunk_by_section("extracted/title-20-404/[file]")
print(f"Generated {len(test_chunks)} chunks")
for chunk in test_chunks[:3]:
    print(f"\nSection: {chunk['section']}")
    print(f"Title: {chunk['title']}")
    print(f"Text length: {len(chunk['text'])} chars")
```

**Verification:** Chunking produces meaningful, self-contained segments

#### 4.3 Token Count Estimation

```python
# token_analysis.py
import tiktoken

enc = tiktoken.encoding_for_model("gpt-4")

def count_tokens(file_path):
    with open(file_path, 'r') as f:
        text = f.read()
    return len(enc.encode(text))

# Count tokens for each title
titles = {
    "Title 38": "extracted/title-38/",
    "Title 20 Part 404": "extracted/title-20-404/",
    "Title 20 Part 416": "extracted/title-20-416/",
    "Title 25 Part 70": "extracted/title-25-70/",
}

for title_name, path in titles.items():
    total_tokens = 0
    file_count = 0

    for file in Path(path).rglob("*.txt"):  # Adjust extension
        total_tokens += count_tokens(file)
        file_count += 1

    print(f"{title_name}:")
    print(f"  Files: {file_count}")
    print(f"  Total tokens: {total_tokens:,}")
    print(f"  Estimated chunks (1000 tokens each): {total_tokens // 1000:,}")
```

**Verification:** Token counts documented for all four titles

#### 4.4 Embedding Pipeline Test

Test with existing embedding pipeline:

```python
# embedding_test.py
import sys
sys.path.append('/ganuda/lib')

from research_client import embed_text  # Or whatever our embedding function is

# Load 10 sample sections
sample_sections = load_sample_sections("extracted/title-38/", limit=10)

# Test embedding
for section in sample_sections:
    embedding = embed_text(section['text'])

    print(f"Section {section['section']}:")
    print(f"  Text length: {len(section['text'])} chars")
    print(f"  Embedding dimension: {len(embedding)}")
    print(f"  Embedding range: [{min(embedding):.3f}, {max(embedding):.3f}]")
```

**Verification:** Embeddings generated successfully for all test sections

### 5. Design Update Pipeline

#### 5.1 Repository Update Mechanism

```bash
# Check if repo has automated updates
cat .github/workflows/*.yml 2>/dev/null
crontab -l | grep ecfr 2>/dev/null

# Check for update scripts
find . -name "*update*" -o -name "*sync*" -o -name "*fetch*"
```

**Document:**
- Is there an automated update mechanism?
- How often does the repo update?
- What triggers updates?

#### 5.2 Official GPO Bulk Data Comparison

Examine official GPO source:

```bash
# Clone GPO bulk data repo for comparison
cd /ganuda/tmp/ecfr-poc
git clone https://github.com/usgpo/bulk-data.git

# Compare structure and formats
ls -la bulk-data/CFR/
ls -la ecfr/

# Check for Title 38 in GPO
find bulk-data/CFR -path "*title-38*" | head -10
```

**Compare:**
| Criterion | ecfr Repo | GPO Bulk Data | Official API |
|-----------|-----------|---------------|--------------|
| Format | [format] | XML | XML/JSON |
| Update frequency | [frequency] | Daily | Real-time |
| Completeness | [assessment] | Complete | Complete |
| Ease of use | [rating] | Complex | Requires auth |
| Historical versions | [yes/no] | Yes | Limited |

#### 5.3 Update Pipeline Design

Design automated update pipeline:

```python
# update_cfr_pipeline.py

"""
Recommended Update Pipeline:

1. SOURCE SELECTION:
   - Primary: [ecfr repo / GPO bulk data / Official API]
   - Fallback: [alternative source]

2. UPDATE FREQUENCY:
   - Daily check for new commits/data
   - Weekly full re-ingestion
   - Monthly validation against official eCFR.gov

3. PROCESS:
   a. Fetch latest data from source
   b. Compare checksums/timestamps with current data
   c. If changed:
      - Extract target titles (38, 20, 25)
      - Chunk for RAG
      - Generate embeddings
      - Update vector store
      - Update metadata (effective dates, citations)
   d. Validate sample sections against eCFR.gov
   e. Alert if validation fails

4. ROLLBACK:
   - Keep previous 3 versions
   - Auto-rollback if >5% of queries return no results

5. MONITORING:
   - Track update success/failure
   - Monitor RAG query quality after updates
   - Alert on data staleness (>30 days)
"""

def check_for_updates():
    """Check if CFR data has been updated"""
    pass

def fetch_and_ingest():
    """Fetch new data and update RAG pipeline"""
    pass

def validate_update():
    """Validate new data against official sources"""
    pass

def rollback_if_needed():
    """Rollback to previous version if validation fails"""
    pass
```

**Verification:** Update pipeline design is complete and automated

### 6. Security Audit (Crawdad Protocol)

```bash
# Search for executable code
find ecfr/ -type f \( -name "*.py" -o -name "*.js" -o -name "*.sh" -o -name "*.exe" -o -name "*.bat" \)

# If executable code found, audit it
for script in $(find ecfr/ -name "*.py"); do
    echo "=== $script ==="
    head -50 "$script"

    # Check for dangerous operations
    grep -n "eval\|exec\|__import__\|compile\|subprocess\|os.system" "$script"
done

# Check for binary files
find ecfr/ -type f -exec file {} \; | grep -i "executable\|binary" | grep -v ".git"

# Check repository reputation
cd ecfr/
git log --oneline --graph --all | head -20
git log --all --format="%aN" | sort | uniq -c | sort -nr  # Top contributors

# Check for suspicious commits
git log --all --grep="backdoor\|malware\|hack" --oneline
```

**Security Assessment:**
- [ ] No suspicious executable code
- [ ] No binary files (except images/docs)
- [ ] Repository has legitimate commit history
- [ ] Contributors are identifiable
- [ ] No obfuscated code
- [ ] No network calls in data files
- [ ] No eval/exec usage

**Verification:** Security audit passed or risks documented

### 7. Write Findings Report

Create `/ganuda/docs/reports/POC-ECFR-FINDINGS-FEB04-2026.md`:

```markdown
# POC Findings: Electronic CFR Data Source Evaluation

**Date:** 2026-02-04
**Evaluated By:** [Jr Name]
**Duration:** [X hours]
**Repository:** https://github.com/AlextheYounga/ecfr

---

## Executive Summary

**Recommendation:** [USE ECFR REPO / USE GPO / USE OFFICIAL API / BUILD SCRAPER]

[2-3 sentences explaining key finding and rationale]

---

## Data Quality Assessment

### Accuracy

| Section Tested | Match Type | Similarity |
|----------------|------------|------------|
| 38 CFR 4.17a | [EXACT/SIMILAR/MISMATCH] | [XX%] |
| 20 CFR 404.1501 | [EXACT/SIMILAR/MISMATCH] | [XX%] |
| 20 CFR 416.920 | [EXACT/SIMILAR/MISMATCH] | [XX%] |
| 25 CFR 70.4 | [EXACT/SIMILAR/MISMATCH] | [XX%] |
| 38 CFR 3.102 | [EXACT/SIMILAR/MISMATCH] | [XX%] |

**Overall Accuracy:** [EXCELLENT / ACCEPTABLE / UNACCEPTABLE]

**Issues Found:**
- [Issue 1]
- [Issue 2]

### Currency

| Title | Repo Date | Official eCFR Date | Delta | Status |
|-------|-----------|-------------------|-------|--------|
| Title 38 | [YYYY-MM-DD] | [YYYY-MM-DD] | [X days] | [OK/STALE] |
| Title 20 | [YYYY-MM-DD] | [YYYY-MM-DD] | [X days] | [OK/STALE] |
| Title 25 | [YYYY-MM-DD] | [YYYY-MM-DD] | [X days] | [OK/STALE] |

**Overall Currency:** [EXCELLENT / ACCEPTABLE / UNACCEPTABLE]

### Cross-References

**Status:** [PRESERVED / PARTIAL / MISSING]

**Examples:**
```
38 CFR 4.130 → 4.132: [working/broken]
20 CFR 404.1520 → 404.1560: [working/broken]
```

### Tables and Charts

**Status:** [INTACT / DEGRADED / MISSING]

**Examples:**
- 38 CFR 4.71a tables: [assessment]
- 20 CFR 404.1046 tables: [assessment]

---

## RAG Suitability

### Data Format

**Format:** [XML / JSON / Plain Text / Markdown]
**Encoding:** [UTF-8 / ASCII / Other]
**Structure:** [Detailed description]

**Sample:**
```
[Paste sample of data format]
```

### Chunking Strategy

**Approach:** [Section-based / Subsection-based / Paragraph-based]
**Average chunk size:** [XXX tokens]
**Chunks preserving context:** [Yes/No/Partial]

**Test Results:**
- Generated [XXX] chunks from Title 38 sample
- [XX%] of chunks are self-contained
- [XX%] require cross-reference lookup

### Token Analysis

| Title | Files | Total Tokens | Estimated Chunks |
|-------|-------|--------------|------------------|
| Title 38 | [count] | [count] | [count] |
| Title 20 Part 404 | [count] | [count] | [count] |
| Title 20 Part 416 | [count] | [count] | [count] |
| Title 25 Part 70 | [count] | [count] | [count] |

**Total RAG corpus size:** [XXX,XXX tokens] ([XXX chunks])

### Embedding Test Results

**Embeddings generated:** [XX/10] successful
**Average embedding time:** [XXX ms]
**Any failures:** [description or "None"]

---

## Update Pipeline

### Current Mechanism

**ecfr Repo:**
- Update frequency: [frequency]
- Automated: [Yes/No]
- Mechanism: [description]

**GPO Bulk Data:**
- Update frequency: Daily
- Automated: Yes
- Mechanism: GitHub Actions

**Official API:**
- Update frequency: Real-time
- Requires: Authentication
- Rate limits: [limits]

### Recommended Approach

**Primary Source:** [ecfr / GPO / Official API]
**Rationale:** [explanation]

**Update Frequency:**
- Check: [frequency]
- Ingest: [frequency]
- Validate: [frequency]

**Pipeline Design:**
```
[Flowchart or description of update pipeline]
```

---

## Security Audit

### Code Audit Results

**Executable files found:** [count]

**Review:**
- [ ] All scripts reviewed
- [ ] No suspicious operations
- [ ] No network calls from data files
- [ ] No eval/exec usage
- [ ] No obfuscated code

**Issues:** [None / Description of issues]

### Repository Reputation

**Created:** [date]
**Stars:** [count]
**Forks:** [count]
**Contributors:** [count]
**Last commit:** [date]

**Assessment:** [TRUSTWORTHY / QUESTIONABLE / UNSAFE]

---

## Comparison Matrix

| Criterion | ecfr Repo | GPO Bulk | Official API | Build Scraper |
|-----------|-----------|----------|--------------|---------------|
| Accuracy | [score] | [score] | [score] | [score] |
| Currency | [score] | [score] | [score] | [score] |
| Format | [score] | [score] | [score] | [score] |
| Ease of Use | [score] | [score] | [score] | [score] |
| Update Cost | [score] | [score] | [score] | [score] |
| Security | [score] | [score] | [score] | [score] |
| **TOTAL** | [XX/30] | [XX/30] | [XX/30] | [XX/30] |

---

## Recommendation

**[USE ECFR REPO / USE GPO / USE OFFICIAL API / BUILD SCRAPER]**

### Rationale

[Detailed explanation of why this option is best]

### Implementation Plan

**If USE ECFR REPO:**
1. Fork repository to ganuda org
2. Set up automated sync (daily)
3. Build chunking pipeline
4. Integrate with existing RAG
5. Set up validation against eCFR.gov
6. Timeline: [X weeks]

**If USE GPO:**
1. Clone GPO bulk-data repo
2. Parse XML format
3. Extract target titles
4. Build chunking pipeline
5. Integrate with existing RAG
6. Timeline: [X weeks]

**If USE OFFICIAL API:**
1. Register for API access
2. Build API client
3. Handle rate limits
4. Build chunking pipeline
5. Integrate with existing RAG
6. Timeline: [X weeks]

**If BUILD SCRAPER:**
1. Design scraper for eCFR.gov
2. Handle pagination and structure
3. Respect robots.txt
4. Build chunking pipeline
5. Integrate with existing RAG
6. Timeline: [X weeks]

### Risks

**High Risk:**
- [Risk 1]

**Medium Risk:**
- [Risk 2]

**Low Risk:**
- [Risk 3]

### Next Steps

1. [Action 1]
2. [Action 2]
3. [Action 3]

---

## Appendices

### A. Sample Data

[Include samples from each title]

### B. Chunking Code

[Include final chunking implementation]

### C. Token Distribution

[Histogram or chart of chunk token sizes]

### D. Validation Scripts

[Include accuracy validation scripts]
```

**Verification:** Report is complete, data-driven, and actionable

### 8. Council Recommendation Package

```markdown
## Council Review Package

**Recommendation:** [USE ECFR REPO / USE GPO / USE OFFICIAL API / BUILD SCRAPER]

**Key Findings:**
1. Accuracy: [assessment with data]
2. Currency: [assessment with data]
3. Ease of integration: [assessment]

**Decision Factors:**
- Data accuracy: [PASS/FAIL]
- Update reliability: [PASS/FAIL]
- Security: [PASS/FAIL]
- Development effort: [X weeks]

**Risk Assessment:**
- Technical risk: [LOW/MEDIUM/HIGH]
- Data quality risk: [LOW/MEDIUM/HIGH]
- Security risk: [LOW/MEDIUM/HIGH]

**Vote Required:** Simple majority (3/5)

**Proposed Timeline:**
- Week 1: Council decision
- Week 2-4: Implementation
- Week 5: Validation and deployment
```

**Verification:** Council package is concise and decision-ready

---

## Constraints

1. **NO Production Changes:** Evaluation only, no RAG modifications
2. **Isolated Environment:** All work in `/ganuda/tmp/ecfr-poc`
3. **Time Box:** Complete in 8 hours or less
4. **Security First:** Crawdad protocol must be followed

---

## Deliverables

1. Complete findings report at `/ganuda/docs/reports/POC-ECFR-FINDINGS-FEB04-2026.md`
2. Council review package
3. Chunking test code
4. Embedding test results
5. Update pipeline design
6. Security audit report

---

## Resources

- ecfr Repository: https://github.com/AlextheYounga/ecfr
- GPO Bulk Data: https://github.com/usgpo/bulk-data
- Official eCFR: https://www.ecfr.gov/
- eCFR API: https://www.federalregister.gov/developers/documentation/api/v1
- Existing RAG pipeline: `/ganuda/assist/[locate embedding code]`

---

## Notes

- Title 38 is large (~thousands of sections) - use sampling for token counts
- GPO XML format is complex but authoritative
- Official API requires registration (may take days)
- Crawling eCFR.gov directly should respect robots.txt and rate limits

---

**Status:** PENDING ASSIGNMENT
**Last Updated:** 2026-02-04
