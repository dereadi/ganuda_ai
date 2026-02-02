# JR Instruction: VetAssist Resources Frontend — Topic-Based Sections with External Links

**Task ID:** VETASSIST-RESOURCES-FRONTEND-001
**Date:** January 31, 2026
**Priority:** P1
**Type:** frontend
**Assigned To:** Software Engineer Jr.
**Depends On:** VETASSIST-RESOURCES-API-001 (Phase 3 — sections endpoint and resource-links endpoint must exist)
**Estimated Steps:** 3

---

## Objective

Transform the VetAssist resources page from a flat grid of articles into a topic-organized knowledge base with 5 browsable sections, each containing articles and curated external links to official VA resources. This is the veteran-facing result of the entire resources pipeline.

---

## Background

The resources page currently displays all 17 articles in a flat 3-column grid with difficulty and tag filters. Phase 3 added two new API endpoints:
- `GET /api/v1/content/sections` — articles grouped by 5 sections (getting-started, building-your-claim, understanding-your-rating, appeals-and-next-steps, special-topics)
- `GET /api/v1/resource-links/by-section` — curated external links grouped by the same 5 sections

The frontend needs to consume these endpoints and render a section-based layout.

**Frontend stack:** Next.js 14, React, Tailwind CSS. The app is at `/ganuda/vetassist/frontend/`.

---

## New Page Structure

```
/resources
├── Hero header (title + description — keep existing)
├── Search bar (searches articles — keep existing)
├── Difficulty filter (keep existing, works within sections)
├── Section: "Getting Started"
│   ├── Section header (display_name + description)
│   ├── Article cards (grid, ordered by section_order)
│   └── "Official VA Resources" box (external links for this section)
├── Section: "Building Your Claim"
│   ├── Section header
│   ├── Article cards
│   └── "Official VA Resources" box
├── Section: "Understanding Your Rating"
│   ├── Section header
│   ├── Article cards
│   └── "Official VA Resources" box
├── Section: "Appeals & Next Steps"
│   ├── Section header
│   ├── Article cards
│   └── "Official VA Resources" box
├── Section: "Special Topics"
│   ├── Section header
│   ├── Article cards
│   └── "Official VA Resources" box
└── Disclaimer footer (keep existing)
```

---

## Steps

### Step 1: Update the resources page layout

**File:** `/ganuda/vetassist/frontend/app/resources/page.tsx`

This is the main change. Replace the flat grid rendering with section-based rendering.

**1A. Add state and fetching for sections data.**

Currently the page fetches from `/api/v1/content`. Change the primary fetch to use `/api/v1/content/sections` and add a second fetch for `/api/v1/resource-links/by-section`.

Add these state variables:

```typescript
const [sections, setSections] = useState<any[]>([]);
const [resourceLinks, setResourceLinks] = useState<Record<string, any[]>>({});
```

Add a new `fetchSections` function:

```typescript
const fetchSections = async () => {
  try {
    setLoading(true);
    const sectionsRes = await fetch(`${API_BASE}/api/v1/content/sections`);
    const sectionsData = await sectionsRes.json();
    setSections(sectionsData.sections || []);

    const linksRes = await fetch(`${API_BASE}/api/v1/resource-links/by-section`);
    const linksData = await linksRes.json();
    setResourceLinks(linksData.sections || {});
  } catch (error) {
    console.error('Failed to fetch sections:', error);
  } finally {
    setLoading(false);
  }
};
```

Call `fetchSections()` in useEffect on mount.

Keep the existing `fetchContent()` function for when search is active — when the user types a search query, switch back to the flat grid view showing search results. When search is cleared, show the section view.

**1B. Add section rendering.**

When search is empty and no tag filter is active, render sections. When search or tag filter is active, fall back to the existing flat grid (filtered results).

For each section, render:

```tsx
{sections.map((section) => {
  // Apply difficulty filter if active
  const filteredArticles = selectedDifficulty === 'all'
    ? section.articles
    : section.articles.filter((a: any) => a.difficulty_level === selectedDifficulty);

  if (filteredArticles.length === 0) return null;

  const sectionLinks = resourceLinks[section.section_id] || [];

  return (
    <div key={section.section_id} className="mb-12">
      {/* Section header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">{section.display_name}</h2>
        <p className="mt-1 text-gray-600">{section.description}</p>
      </div>

      {/* Article cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
        {filteredArticles.map((item: any) => (
          // Use existing article card rendering — same card JSX that's already in the page
          <ArticleCard key={item.id} item={item} />
        ))}
      </div>

      {/* Official VA Resources box */}
      {sectionLinks.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-blue-800 mb-3 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            Official VA Resources
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {sectionLinks.map((link: any) => (
              <a
                key={link.id}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-start gap-2 p-2 rounded hover:bg-blue-100 transition-colors"
              >
                <svg className="w-4 h-4 mt-0.5 text-blue-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                <div>
                  <span className="text-sm font-medium text-blue-700 hover:text-blue-900">{link.title}</span>
                  {link.source_org && (
                    <span className="block text-xs text-blue-500">{link.source_org}</span>
                  )}
                </div>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
})}
```

**1C. Extract the article card into a reusable component.**

The existing article card JSX is inline in the map function. Extract it so both the section view and the flat grid search results view can use it:

```tsx
function ArticleCard({ item }: { item: any }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow p-6 flex flex-col">
      {/* Keep existing card content exactly as-is */}
      {/* difficulty badge, read time, title, summary, tags, view count */}
    </div>
  );
}
```

**1D. Conditional rendering logic.**

```tsx
{/* Section view (default) */}
{!searchQuery && !selectedTag && sections.length > 0 && (
  // Render sections with articles and external links
)}

{/* Flat grid view (search/filter active) */}
{(searchQuery || selectedTag) && (
  // Render existing flat grid with content items
)}
```

### Step 2: Update the article detail page with section context

**File:** `/ganuda/vetassist/frontend/app/resources/[id]/page.tsx`

**2A. Update the breadcrumb** to show section name.

The API now returns `section` for each article. Use it in the breadcrumb:

```tsx
{/* Before: Home > Resources > Article Title */}
{/* After:  Home > Resources > Section Name > Article Title */}
{article.section && (
  <span className="text-gray-500">
    <span className="mx-2">/</span>
    <Link href={`/resources#${article.section}`} className="hover:text-blue-600">
      {sectionDisplayNames[article.section] || article.section}
    </Link>
  </span>
)}
```

Add the section display name mapping:

```typescript
const sectionDisplayNames: Record<string, string> = {
  'getting-started': 'Getting Started',
  'building-your-claim': 'Building Your Claim',
  'understanding-your-rating': 'Understanding Your Rating',
  'appeals-and-next-steps': 'Appeals & Next Steps',
  'special-topics': 'Special Topics',
};
```

**2B. Show author and last updated date.**

Add below the article header:

```tsx
<div className="text-sm text-gray-500 mt-2">
  {article.author && <span>By {article.author}</span>}
  {article.updated_at && (
    <span className="ml-4">Updated {new Date(article.updated_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</span>
  )}
</div>
```

**2C. Add source references display.**

If the article has `source_references`, show them in a small box after the content:

```tsx
{article.source_references && article.source_references !== 'N/A (platform guide)' && (
  <div className="mt-6 p-3 bg-gray-50 rounded-lg border border-gray-200">
    <span className="text-xs font-semibold text-gray-500 uppercase">Regulatory References</span>
    <p className="text-sm text-gray-700 mt-1">{article.source_references}</p>
  </div>
)}
```

### Step 3: Verify

After the changes, rebuild the frontend:

```bash
cd /ganuda/vetassist/frontend
npm run build
cp -r .next/static .next/standalone/.next/static
# Restart the frontend service
```

Then verify:

1. Navigate to `https://vetassist.ganuda.us/resources` — articles should appear in 5 topic sections
2. Each section should have a header with display name and description
3. Each section should have an "Official VA Resources" blue box with external links
4. External links should open in new tabs
5. Difficulty filter should still work (filters within sections)
6. Search should switch to flat grid view showing matching results
7. Click any article — detail page should show section breadcrumb, author, updated date, and source references
8. Related articles should still work
9. All external links should have the external link icon

---

## Success Criteria

- [ ] Resources page shows 5 named sections in order: Getting Started, Building Your Claim, Understanding Your Rating, Appeals & Next Steps, Special Topics
- [ ] Each section has a header with display name and description
- [ ] Articles within each section are ordered by `section_order`
- [ ] Each section has an "Official VA Resources" box with curated external links
- [ ] External links open in new tabs with `rel="noopener noreferrer"`
- [ ] Difficulty filter works within sections (hides sections with no matching articles)
- [ ] Search switches to flat grid view
- [ ] Article detail page shows section in breadcrumb
- [ ] Article detail page shows author and last updated date
- [ ] Article detail page shows source references (regulatory citations)
- [ ] Frontend builds without errors
- [ ] No console errors in browser

---

## Files

| File | Action | Purpose |
|------|--------|---------|
| `/ganuda/vetassist/frontend/app/resources/page.tsx` | MODIFY | Section-based layout with external links |
| `/ganuda/vetassist/frontend/app/resources/[id]/page.tsx` | MODIFY | Section breadcrumb, author, source refs |

---

*Cherokee AI Federation — For Seven Generations*
