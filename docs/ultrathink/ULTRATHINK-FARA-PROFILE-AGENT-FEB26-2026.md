# ULTRATHINK: FARA Profile Agent — "Promote the Chief"

**Date**: February 26, 2026
**Triggered By**: Two full reconnaissance passes of workatastartup.com profile, React form combat
**Council Vote**: Pending (inline deliberation below)
**Thermal**: To be recorded on completion

---

## Situation Assessment

The Chief's workatastartup.com profile is partially complete. Two sessions of manual form manipulation revealed both the site's full structure and the React form patterns that work vs. don't. Current state:

### What's DONE
| Tab | Status | Notes |
|-----|--------|-------|
| Personal Info | COMPLETE | Name, email, phone, LinkedIn |
| Location | COMPLETE | Bentonville AR, US authorized, remote, no relocate |
| Role | COMPLETE | Engineering (ML, DevOps, Backend, Full Stack), 30 years, GitHub |
| Career | COMPLETE | Small/Medium preferred, equity interested, $150K min |
| Share | COMPLETE | Professional pitch, Cherokee AI Federation story |

### What's BROKEN
| Tab | Status | Issue |
|-----|--------|-------|
| Experience | PARTIALLY BROKEN | Walmart entry OK (summary, dates). Military entry has dates/summary in form but company name and title fields EMPTY (React controlled inputs reject programmatic value setting). A garbage education entry may exist. is_current checkbox still checked for Walmart. |
| Skills | NEEDS SWAP | Has 10/10: Bash, C, Docker, Distributed Systems, InfoSec, macOS, Linux, ML, SQL, PostgreSQL. Need to swap macOS/SQL for Python/Ansible. Previous attempt failed because Enter key hit Save instead of selecting dropdown. |
| Resume | OUTDATED | v5 Dossier uploaded. v8 exists on bmasass (33KB PDF, Feb 18 2026) with full career arc including Jane Street puzzle, Iraq deployment, Remedy 6M tx/day. |

---

## Critical Discovery: `execCommand('insertText')` Bypasses React

**Tested and confirmed**: `document.execCommand('insertText', false, 'text')` returns `true` and the value persists in React state. This is the canonical React form bypass because:

1. It goes through the browser's native text input pipeline
2. React's synthetic event system picks it up as a real user keystroke
3. The `_valueTracker` is updated automatically
4. No need for `nativeSetter`, `InputEvent`, or `simulated = true` hacks

### Pattern That WORKS (all field types)
```javascript
// For text inputs (Employer Name, Title — the ones that were failing)
element.focus();
element.select();  // Select all existing text
document.execCommand('insertText', false, 'new value');

// For textareas
textarea.focus();
textarea.select();
document.execCommand('insertText', false, 'new multiline\nvalue');

// For selects — _valueTracker trick still works fine
var tracker = select._valueTracker;
if (tracker) tracker.setValue(select.value);
select.value = 'new_option';
select.dispatchEvent(new Event('change', { bubbles: true }));
```

### Patterns That FAILED (documented for future reference)
| Approach | Result | Why |
|----------|--------|-----|
| `element.value = x` + input event | Value reverts on React re-render | React overwrites DOM from state |
| `nativeSetter.call(element, x)` | "missing value" in AppleScript | AppleScript can't handle the prototype chain |
| `_valueTracker` on text inputs | Works for textareas/selects, NOT text inputs | Different React fiber binding on text inputs without `name` attr |
| `InputEvent` with `insertText` type | "missing value" | Same AppleScript prototype issue |
| `KeyboardEvent` simulation | Not tested | Too slow for long strings |

---

## Resume Intelligence

### Available Versions (Verified)
| Version | Location | Size | Date | Format |
|---------|----------|------|------|--------|
| Dossier v8 | bmasass:/Users/Shared/ganuda/docs/ | 33KB | Feb 18 | PDF + MD |
| Dossier v7 | bmasass:/Users/dereadi/Documents/ | 32KB | Feb 17 | PDF |
| Dossier v6 | sasass:/Users/dereadi/Documents/ + /Users/Shared/ganuda/docs/ | 30KB | Feb 14 | PDF + MD |
| Security v9 | sasass:/Users/dereadi/Documents/ | 7KB | Feb 13 | PDF |
| Jan 2026 Resume | sasass:/Users/dereadi/Desktop/ | — | Jan 2026 | MD |
| MultiAgent Dec25 | bmasass:/Users/Shared/ganuda/data/resumes/ | — | Dec 2025 | MD + PDF |

### v8 Dossier Content (Best Available)
The v8 is the most comprehensive, containing:
- Full origin story (encyclopedia at 12, ASVAB 98th percentile)
- Air Force (1987-1990): Command & Control, Thunderbird incident
- Army Guard (1993-2013): C-1-142 FA, MLRS, token ring on rocket launchers
- Iraq (Title 10, Nov 2005 - Mar 2007): Camp Cropper, Squad Leader 13 soldiers
- Walmart arc (1990-2024): Rx Help Desk → Telecom → Remedy (6M tx/day, 8hr→4hr migration) → Unix → Security (SOC/IR/forensics lab, SureView South Africa weekend, air-gapped work)
- Sovereign AI Federation: 6-node cluster, 7-specialist council, 88K+ thermal memories
- Jane Street puzzle: Solved 10^122 search space, MSE zero, 44th solver
- Operating philosophy and patterns

### Resume Accuracy Report (Nov 2025)
Thermal #verified — ZERO FABRICATIONS confirmed by Triad. Section 10 lists rejected claims. All hardware specs verified from live `nvidia-smi`/`lscpu`. Constitutional attestation at 95C.

### What the Jan 2026 Resume Gets WRONG
- Lists rank as E7/SFC and 26 years — Chief says 23 years, E-6 (SSG)
- Shows "December 2016 - Present" for SIMS — should be May 2024 departure
- Lists SNHU B.S. Cyber Security "In Progress" — need to verify current status
- Several certifications listed (CUDA, PyTorch, Healthcare Privacy, PostgreSQL) — verify if these are formal certs or course completions
- States "retired with honors after 26 years of distinguished service" — Chief said 23 years

### Corrected Facts (From Chief, This Session)
- **Air Force**: 1987-1990, Command and Control Specialist
- **Army National Guard**: 1993-2013 (20 years Guard)
- **Iraq Title 10 orders**: Nov 2005 - Mar 2007, train-up at Fort Dix
- **Total military**: 23 years combined (3 AF + 20 Guard, gap 1990-1993)
- **Rank progression**: E-3 (joined Guard) → E-4 (7 years, knew systems but wasn't playing promotion game) → E-5 (2003) → E-6/SSG (promoted for Iraq, Squad Leader 13 soldiers) → E-7/SFC (promoted after Iraq) → Master Gunner school (M270/M270A1, Battalion weapons SME) → Platoon Sergeant (~40 soldiers, section chiefs on 4 MLRS systems) → Retired 2013
- **Final rank**: E-7 (SFC), Platoon Sergeant. NOT E-6 as initially stated — E-6 was Iraq rank only.
- **Jan 2026 resume was CORRECT about E-7/SFC and Platoon Sergeant** — Coyote's flag was wrong
- **23 years is correct** (not 26 — the 3-year gap 1990-1993 matters)
- **Walmart**: ~1990-2024 (34 years), departed May 2024

---

## Battle Plan

### Phase 1: Generate Updated Resume PDF (10 min)

**Goal**: Create a corrected PDF combining the best content from all versions with verified facts.

**Source Material Priority**:
1. Dossier v8 (MD) — narrative voice, most comprehensive
2. Thermal memory origin stories (#101921-101925) — verified career details
3. Resume facts report — constitutional attestation, rejected claims
4. Chief's corrections this session — dates, rank, years of service

**Key Corrections to Apply**:
- E-6 (SSG) not E-7 (SFC)
- 23 years total military, not 26
- Guard 1993-2013, not 1987-2013
- Air Force 1987-1990
- Walmart ended May 2024
- Remove "retired with honors" language (his phrase was more understated)

**Output**: Generate corrected MD on redfin → convert to PDF via pandoc or wkhtmltopdf → scp to sasass Desktop for upload.

### Phase 2: Upload Resume (5 min)

**Approach**: The "click here" link (href ending in `#`) likely opens a file dialog or modal. Options:
1. Click the link → see what modal/dialog appears → use AppleScript to interact with file dialog
2. If it creates a `<input type="file">`, programmatically set its files
3. Fallback: Use AppleScript `keystroke` to navigate Finder file dialog

**Upload path**: Use the PDF from sasass Desktop (either scp'd there from bmasass, or generated fresh).

### Phase 3: Fix Experience Page (15 min)

**Using the `execCommand('insertText')` pattern that WORKS:**

```javascript
function setField(element, value) {
    element.focus();
    element.select();  // Select all existing content
    document.execCommand('insertText', false, value);
}
```

**Step 3a: Clean up the form**
- Remove the garbage education entry (if it exists)
- Remove the broken military work history entry (empty company/title)
- Verify Walmart entry is intact

**Step 3b: Add military work history**
- Click "add another" under Work History (first `button.add-button`)
- Wait for new fields to render
- Use `execCommand` to fill: Employer, Title, Location
- Use `_valueTracker` for selects (dates) and textarea (summary)
- Uncheck is_current on Walmart

**Step 3c: Field values**

**Military Entry:**
- Employer: `US Air Force / Arkansas Army National Guard`
- Title: `Sergeant First Class (E-7) — Platoon Sergeant, Master Gunner, Squad Leader`
- Location: `Little Rock AFB, AR / Rogers, AR / Iraq`
- Dates: Jun 1987 - Jun 2013
- is_current: unchecked
- Summary: 23 years combined service. AF: Command & Control (1987-90). Guard: C-1-142 FA, M110→MLRS, telecom, token ring on rocket launchers. Iraq (Title 10 Nov 05-Mar 07): 39th IBCT, Fort Dix, Camp Cropper/Abu Ghraib, Squad Leader 13 soldiers. Post-Iraq: promoted E-7, Master Gunner school (M270/M270A1 Battalion weapons SME), Platoon Sergeant (~40 soldiers). Most awarded platoon through disciplined documentation.

**Walmart Entry** (verify/fix):
- Employer: `Walmart` (already set)
- Title: `Senior Systems Engineer` (already set)
- Location: `Bentonville, AR` (fix if corrupted)
- Dates: Nov 1990 - May 2024 (verify)
- is_current: UNCHECK (he left May 2024)
- Summary: (already set, verify intact)

**Education** (verify):
- School: NorthWest Arkansas Community College (already set)
- Field: Computer Science
- Degree: Associate of Science (AS)
- Dates: 1996-2000

### Phase 4: Fix Skills (5 min)

**Strategy**: Remove macOS and SQL, add Python and Ansible.

**The Enter Key Problem**: When the skills dropdown is open, pressing Enter hits the Save button instead of selecting the highlighted option.

**New approach using execCommand**:
1. Click the skills input to open dropdown
2. Type "Python" using `execCommand('insertText')`
3. Wait for dropdown to filter
4. Instead of Enter, use `element.click()` on the dropdown option directly:
   ```javascript
   var options = document.querySelectorAll('[class*=option]');
   options.forEach(function(o) {
       if (o.textContent.includes('Python')) o.click();
   });
   ```
5. Repeat for Ansible

**Removal**: Click the `x` button on the macOS and SQL skill chips (React multiValue remove — this worked in the previous session).

### Phase 5: Preview and Verify (5 min)

- Navigate to profile preview ("Want to know what your profile looks like to YC companies? Click here to preview it.")
- Capture screen or read DOM to verify all sections render correctly
- Report back to Chief with full profile summary

---

## Council Deliberation (Inline)

**Medicine Woman**: The corrected facts honor the Chief's actual path — self-taught, 23 years military not 26, E-6 not E-7. The dossier v8 narrative voice is authentic ("no degree, no linear path, just the next problem"). Don't sanitize it for corporate consumption. YC founders appreciate raw authenticity over polished corporate speak.

**Coyote**: The `execCommand` discovery changes everything. Stop fighting React — speak its language. The real question is: does workatastartup.com even PARSE uploaded resumes into form fields, or just attach the PDF? If it parses, uploading v8 might auto-fill Experience. Test the upload link FIRST before manually filling fields. Also: the Jan 2026 resume has fabricated rank (E-7) and years (26) — who wrote that? Flag it.

**Raven**: Strategic sequencing matters. Upload the corrected resume FIRST — that's what hiring managers actually read. The Experience form fields are supplementary (for scrapers, as the Chief noted). Don't spend 30 minutes perfecting form fields that nobody reads when the resume PDF is the real artifact. Priority: resume PDF > Experience page > Skills swap.

**Turtle**: Seven generations — the resume accuracy report exists for a reason. Every claim must trace to thermal memory or system verification. The E-7/26-year error propagated across 3+ resume versions. Fix it at the source (generate a corrected master) so it doesn't spread further.

**Eagle Eye**: The form currently has corrupted state (military title in Walmart location field, empty military employer). Clean start: remove the broken military entry, verify Walmart is clean, THEN add military fresh.

---

## Execution Order

1. **Read current form state** — assess damage from previous attempts
2. **Clean the form** — remove broken entries, verify Walmart intact
3. **Generate corrected resume PDF** — v9 with verified facts, on redfin
4. **Transfer PDF to sasass** — scp to Desktop
5. **Upload resume** — click upload link, interact with file dialog
6. **Add military work history** — using `execCommand('insertText')`
7. **Fix Walmart entry** — uncheck is_current, verify location
8. **Fix Skills** — remove macOS/SQL, add Python/Ansible via option click
9. **Preview profile** — capture and verify
10. **Record thermal memory** — profile completion milestone

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| execCommand might not work for all fields | Tested and confirmed on the actual page. Fallback: AppleScript keystroke simulation |
| Resume upload might not exist as file input | The link is `#` anchor — may be JavaScript modal. Inspect what happens on click. Fallback: manual upload by Chief |
| PDF generation fails on redfin | pandoc is installed. Fallback: use existing v8 PDF from bmasass with known inaccuracies noted |
| Form state corrupted beyond repair | Nuclear option: reload the page (URL navigation), lose all unsaved changes, start fresh. Walmart summary is the main thing to preserve (copy to clipboard first) |
| Skills dropdown option click doesn't work | Fallback: Have Chief manually add Python/Ansible (2 clicks each) |

---

## Success Criteria

- [ ] Resume v9 PDF uploaded (corrected E-6, 23 years, May 2024 departure)
- [ ] Military work history: company, title, location, dates, summary all populated
- [ ] Walmart work history: correct dates, is_current unchecked, summary intact
- [ ] Skills: Python and Ansible added, macOS and SQL removed
- [ ] Profile preview shows complete, professional presentation
- [ ] Thermal memory recorded with completion details
