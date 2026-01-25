# JR Task Assignment: Crawl and Validate All Links
**Date:** December 27, 2025
**Platform:** Bluefin (192.168.132.222)
**Project:** Ganuda VetAssist Platform
**Phase:** Link Validation & QA

---

## Context

After JR 21 and JR 22 complete their code fixes, we need to verify that:
- All pages render correctly
- All internal links work
- All external links are valid
- Navigation flows correctly
- No broken links or 404 errors
- Accessibility features work as expected

**JR 23: Crawl the built VetAssist site and validate all links**

---

## JR 23: Site Crawler and Link Validator
**Priority:** HIGH
**Dependencies:** JR 21 and JR 22 fixes complete
**Platform:** Bluefin

**Objectives:**
1. Build the Next.js frontend
2. Start development server
3. Crawl all pages recursively
4. Validate all internal links (navigation, buttons, etc.)
5. Check all external links (VA.gov, etc.)
6. Verify forms submit correctly
7. Test navigation flows
8. Report any broken links or issues

---

## Technical Requirements

### Pages to Crawl

**Public Pages:**
1. `/` - Landing page
2. `/calculator` - VA Disability Calculator
3. `/calculator/examples` - Calculator test cases
4. `/chat` - AI Chatbot (requires auth)
5. `/resources` - Educational content library
6. `/resources/[slug]` - Individual articles (9 articles)
7. `/login` - Login page
8. `/register` - Registration page

**Expected Total:** ~20+ pages (including all resource articles)

### Link Types to Validate

**Internal Links:**
- Navigation links (header, footer)
- Button clicks (Add Condition, Send Message, etc.)
- Resource cards
- Chat sessions
- Breadcrumbs
- Form submissions

**External Links:**
- VA.gov references
- Citation links (38 CFR regulations)
- Documentation links
- Social media (if any)

---

## Implementation Approach

### Option 1: Use Existing Tool (Recommended)

**Install broken-link-checker:**
```bash
cd /ganuda/vetassist/frontend
npm install --save-dev broken-link-checker
```

**Create validation script:**
`/ganuda/vetassist/frontend/scripts/validate-links.js`

```javascript
const blc = require('broken-link-checker');
const fs = require('fs');

const results = {
  scanned: [],
  broken: [],
  working: [],
  skipped: []
};

const siteChecker = new blc.SiteChecker({
  excludeExternalLinks: false,
  filterLevel: 3,
  honorRobotExclusions: false,
  maxSocketsPerHost: 10
}, {
  // Page handler
  page: (error, pageUrl) => {
    if (error) {
      console.error(`❌ Error crawling ${pageUrl}: ${error}`);
    } else {
      console.log(`✓ Scanned: ${pageUrl}`);
      results.scanned.push(pageUrl);
    }
  },

  // Link handler
  link: (result) => {
    if (result.broken) {
      console.error(`❌ BROKEN: ${result.url.original} (on ${result.base.original})`);
      console.error(`   Reason: ${result.brokenReason}`);
      results.broken.push({
        link: result.url.original,
        page: result.base.original,
        reason: result.brokenReason,
        statusCode: result.http?.statusCode
      });
    } else if (result.excluded) {
      results.skipped.push(result.url.original);
    } else {
      results.working.push(result.url.original);
    }
  },

  // Site complete
  end: () => {
    console.log('\n' + '='.repeat(80));
    console.log('LINK VALIDATION COMPLETE');
    console.log('='.repeat(80));
    console.log(`Pages scanned: ${results.scanned.length}`);
    console.log(`Working links: ${results.working.length}`);
    console.log(`Broken links: ${results.broken.length}`);
    console.log(`Skipped links: ${results.skipped.length}`);

    if (results.broken.length > 0) {
      console.log('\n❌ BROKEN LINKS FOUND:');
      results.broken.forEach(link => {
        console.log(`  - ${link.link}`);
        console.log(`    On page: ${link.page}`);
        console.log(`    Reason: ${link.reason}`);
        console.log('');
      });
    }

    // Write results to file
    fs.writeFileSync(
      '/ganuda/vetassist/link-validation-results.json',
      JSON.stringify(results, null, 2)
    );

    console.log('\nResults saved to: /ganuda/vetassist/link-validation-results.json');

    // Exit with error if broken links found
    process.exit(results.broken.length > 0 ? 1 : 0);
  }
});

// Start crawling
const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
console.log(`Starting link validation for: ${BASE_URL}`);
console.log('='.repeat(80) + '\n');

siteChecker.enqueue(BASE_URL);
```

**Add to package.json:**
```json
{
  "scripts": {
    "validate-links": "node scripts/validate-links.js"
  }
}
```

---

### Option 2: Custom Python Crawler

**Create custom crawler:**
`/ganuda/vetassist/scripts/crawl_and_validate.py`

```python
#!/usr/bin/env python3
"""
VetAssist Link Crawler and Validator
Crawls all pages and validates internal/external links
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import sys
from collections import defaultdict

class LinkValidator:
    def __init__(self, base_url):
        self.base_url = base_url
        self.visited = set()
        self.to_visit = {base_url}
        self.broken_links = []
        self.working_links = []
        self.external_links = []

    def is_internal(self, url):
        """Check if URL is internal to the site"""
        return urlparse(url).netloc == urlparse(self.base_url).netloc

    def crawl(self):
        """Crawl all pages starting from base_url"""
        while self.to_visit:
            url = self.to_visit.pop()

            if url in self.visited:
                continue

            print(f"Crawling: {url}")
            self.visited.add(url)

            try:
                response = requests.get(url, timeout=10)

                if response.status_code != 200:
                    self.broken_links.append({
                        'url': url,
                        'status': response.status_code,
                        'type': 'page'
                    })
                    continue

                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find all links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    absolute_url = urljoin(url, href)

                    # Skip mailto, tel, etc.
                    if absolute_url.startswith(('mailto:', 'tel:', 'javascript:')):
                        continue

                    # Check if internal
                    if self.is_internal(absolute_url):
                        if absolute_url not in self.visited:
                            self.to_visit.add(absolute_url)
                    else:
                        self.external_links.append(absolute_url)

            except Exception as e:
                self.broken_links.append({
                    'url': url,
                    'error': str(e),
                    'type': 'error'
                })

    def validate_external_links(self):
        """Validate external links"""
        print(f"\nValidating {len(set(self.external_links))} external links...")

        for url in set(self.external_links):
            try:
                response = requests.head(url, timeout=5, allow_redirects=True)
                if response.status_code >= 400:
                    self.broken_links.append({
                        'url': url,
                        'status': response.status_code,
                        'type': 'external'
                    })
                else:
                    self.working_links.append(url)
            except Exception as e:
                self.broken_links.append({
                    'url': url,
                    'error': str(e),
                    'type': 'external_error'
                })

    def generate_report(self):
        """Generate validation report"""
        report = {
            'pages_crawled': len(self.visited),
            'working_links': len(self.working_links),
            'broken_links': len(self.broken_links),
            'external_links_checked': len(set(self.external_links)),
            'broken_link_details': self.broken_links
        }

        # Print report
        print("\n" + "="*80)
        print("LINK VALIDATION REPORT")
        print("="*80)
        print(f"Pages crawled: {report['pages_crawled']}")
        print(f"Working links: {report['working_links']}")
        print(f"Broken links: {report['broken_links']}")
        print(f"External links checked: {report['external_links_checked']}")

        if self.broken_links:
            print("\n❌ BROKEN LINKS:")
            for link in self.broken_links:
                print(f"  - {link['url']}")
                print(f"    Type: {link['type']}")
                if 'status' in link:
                    print(f"    Status: {link['status']}")
                if 'error' in link:
                    print(f"    Error: {link['error']}")
                print()

        # Save report
        with open('/ganuda/vetassist/link-validation-report.json', 'w') as f:
            json.dump(report, f, indent=2)

        print("\nReport saved to: /ganuda/vetassist/link-validation-report.json")

        return len(self.broken_links) == 0

if __name__ == '__main__':
    base_url = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:3000'

    validator = LinkValidator(base_url)
    validator.crawl()
    validator.validate_external_links()
    success = validator.generate_report()

    sys.exit(0 if success else 1)
```

---

## Execution Steps

**Step 1: Build Frontend**
```bash
cd /ganuda/vetassist/frontend
npm run build
```

**Step 2: Start Server**
```bash
# Terminal 1: Start backend
cd /ganuda/vetassist/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001

# Terminal 2: Start frontend
cd /ganuda/vetassist/frontend
npm run start  # Uses production build
```

**Step 3: Run Link Validation**

**Option 1 (Node.js):**
```bash
cd /ganuda/vetassist/frontend
npm run validate-links
```

**Option 2 (Python):**
```bash
pip install requests beautifulsoup4
python3 /ganuda/vetassist/scripts/crawl_and_validate.py http://localhost:3000
```

---

## Manual Testing Checklist

In addition to automated link checking, manually verify:

### Navigation Flow
- [ ] Click through all nav links in header
- [ ] Test footer links
- [ ] Breadcrumb navigation works
- [ ] Back button works correctly

### Calculator Page
- [ ] Add condition button works
- [ ] Remove condition button works
- [ ] Form submission works
- [ ] Results display correctly
- [ ] Examples page loads

### Chat Page
- [ ] New chat button creates session
- [ ] Session selection works
- [ ] Message sending works
- [ ] Delete session works
- [ ] Copy message button works

### Resources Page
- [ ] Search works
- [ ] Filter buttons work
- [ ] Article cards click through
- [ ] Individual articles load
- [ ] Related articles links work

### Auth Pages
- [ ] Login form works
- [ ] Register form works
- [ ] Validation errors show
- [ ] Redirect after login works

---

## Success Criteria

**Link validation is successful when:**
1. ✅ All pages load without errors
2. ✅ Zero broken internal links
3. ✅ All navigation flows work
4. ✅ External links are valid (VA.gov, etc.)
5. ✅ Forms submit correctly
6. ✅ No 404 errors
7. ✅ No console errors
8. ✅ All images load (if any)

**If any links are broken:**
- Document which pages
- Identify the broken links
- Recommend fixes
- Re-run validation after fixes

---

## Deliverables

**JR 23 must deliver:**

1. **Link Validation Results**
   - `/ganuda/vetassist/link-validation-results.json` or
   - `/ganuda/vetassist/link-validation-report.json`

2. **Validation Report**
   - `/ganuda/vetassist/docs/JR23_LINK_VALIDATION_REPORT.md`

   ```markdown
   # Link Validation Report - JR 23

   ## Summary
   - Pages crawled: X
   - Internal links checked: Y
   - External links checked: Z
   - Broken links found: 0 (or list them)

   ## Broken Links (if any)
   1. URL: ...
      Page: ...
      Reason: ...

   ## Navigation Flows Tested
   - [ ] Landing → Calculator
   - [ ] Landing → Chat
   - [ ] Landing → Resources
   - [ ] Calculator → Examples
   - [ ] Resources → Article → Back
   - [ ] Login → Redirect

   ## Recommendations
   - Fix link X on page Y
   - Update broken external link Z

   ## Status
   ✅ PASS - All links working
   ❌ FAIL - X broken links found
   ```

3. **Screenshots** (optional)
   - Screenshot of working pages
   - Screenshot of validation output

---

## Timeline

**Target: Complete in 1-2 hours**

- Setup and build: 15 minutes
- Automated crawl: 15 minutes
- Manual testing: 30 minutes
- Report writing: 15 minutes

**After validation:** If PASS, proceed to JR 18 deployment

---

## Notes

- **Test with production build** (`npm run build` then `npm run start`)
- **Check console for errors** - open browser dev tools
- **Test different browsers** - Chrome, Firefox, Safari (if available)
- **Test mobile responsiveness** - use dev tools mobile emulator
- **Document any warnings** - even if not breaking

---

## For the Seven Generations.

**Big Mac (TPM) - Ganuda AI**
**December 27, 2025**
