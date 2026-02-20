# Jr Instruction: VetAssist Crisis Resources Tab

**ID:** JR-VETASSIST-CRISIS-RESOURCES-TAB-FEB06-2026
**Priority:** P1-B (Phase 1)
**Estimated Effort:** 2-3 hours
**Council Approval:** Conditional Approve (79.4%, audit hash: 0cc1c5d0138a8d6d)
**Ultrathink Reference:** ULTRATHINK-VETASSIST-PHASE1-ENHANCEMENTS-FEB06-2026.md

---

## Objective

Create a static Crisis Resources page for VetAssist with comprehensive veteran mental health and crisis resources. This is NOT AI-driven crisis detection — it's a resource page for veterans who may be helping a friend in crisis or who need support themselves.

---

## Context

Veterans using VetAssist are primarily checking benefits or seeking rating increases — they are generally not in crisis. However, the site should be prepared for:
- A veteran helping a friend in crisis
- A veteran whose benefits denial triggers distress
- Family members using the site on behalf of a veteran

The page should be **visible but not intrusive** — a navigation tab, not a popup.

---

## Files to Create

### 1. Frontend Page Component

**Path:** `/ganuda/vetassist/frontend/app/crisis-resources/page.tsx`

```tsx
import { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Crisis Resources | VetAssist',
  description: 'Mental health and crisis resources for veterans and their families',
}

export default function CrisisResourcesPage() {
  return (
    <main className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      {/* Hero Section - High Visibility */}
      <div className="max-w-3xl mx-auto">
        <div className="bg-red-50 border-l-4 border-red-600 p-6 mb-8 rounded-r-lg">
          <h1 className="text-2xl font-bold text-red-800 mb-2">
            If you or someone you know is in crisis
          </h1>
          <p className="text-red-700 mb-4">
            The Veterans Crisis Line is available 24/7, 365 days a year.
          </p>

          {/* Primary CTA */}
          <div className="flex flex-col sm:flex-row gap-4">
            <a
              href="tel:988"
              className="inline-flex items-center justify-center px-6 py-3 bg-red-600 text-white font-bold rounded-lg hover:bg-red-700 transition-colors"
            >
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 006.105 6.105l.774-1.548a1 1 0 011.059-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z" />
              </svg>
              Call 988, Press 1
            </a>
            <a
              href="sms:838255"
              className="inline-flex items-center justify-center px-6 py-3 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 transition-colors"
            >
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
              </svg>
              Text 838255
            </a>
            <a
              href="https://www.veteranscrisisline.net/get-help-now/chat/"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center px-6 py-3 bg-green-600 text-white font-bold rounded-lg hover:bg-green-700 transition-colors"
            >
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
              </svg>
              Chat Online
            </a>
          </div>

          <p className="text-sm text-red-600 mt-4">
            TTY: 1-800-799-4889
          </p>
        </div>

        {/* Additional Crisis Resources */}
        <section className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Additional Support Resources
          </h2>

          <div className="grid gap-4 md:grid-cols-2">
            <ResourceCard
              title="Vet Centers"
              description="Community-based counseling for veterans and families. No VA enrollment required."
              link="https://www.vetcenter.va.gov/"
              phone="1-877-927-8387"
            />
            <ResourceCard
              title="Make The Connection"
              description="Real stories from veterans who have faced challenges and found support."
              link="https://www.maketheconnection.net/"
            />
            <ResourceCard
              title="National Alliance on Mental Illness (NAMI)"
              description="Support groups and resources for mental health conditions."
              link="https://www.nami.org/Your-Journey/Veterans-Active-Duty"
              phone="1-800-950-6264"
            />
            <ResourceCard
              title="Give an Hour"
              description="Free mental health services for veterans and their families."
              link="https://giveanhour.org/"
            />
            <ResourceCard
              title="Real Warriors Campaign"
              description="Resources for service members dealing with invisible wounds."
              link="https://www.realwarriors.net/"
            />
            <ResourceCard
              title="Cohen Veterans Network"
              description="Mental health clinics serving post-9/11 veterans and families."
              link="https://www.cohenveteransnetwork.org/"
            />
          </div>
        </section>

        {/* Native/Cherokee Veteran Resources */}
        <section className="bg-amber-50 rounded-lg shadow p-6 mb-8 border border-amber-200">
          <h2 className="text-xl font-semibold text-amber-900 mb-2">
            Native American Veteran Resources
          </h2>
          <p className="text-amber-800 mb-4">
            Culturally-aligned support for Native veterans and their families.
          </p>

          <div className="grid gap-4 md:grid-cols-2">
            <ResourceCard
              title="Native Connections (SAMHSA)"
              description="Suicide prevention and mental health resources for Native communities."
              link="https://www.samhsa.gov/native-connections"
            />
            <ResourceCard
              title="One Sky Center"
              description="National resource center for American Indian and Alaska Native health."
              link="https://www.oneskycenter.org/"
            />
            <ResourceCard
              title="Tribal Veterans Service Officers"
              description="Contact your tribal nation for culturally-specific veteran services."
              link="https://www.va.gov/vso/"
            />
            <ResourceCard
              title="We R Native"
              description="Health resources and community for Native youth and young adults."
              link="https://www.wernative.org/"
            />
          </div>
        </section>

        {/* Helping Someone Else */}
        <section className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Helping a Veteran in Crisis
          </h2>

          <div className="prose prose-blue max-w-none">
            <h3 className="text-lg font-medium text-gray-900">Warning Signs</h3>
            <ul className="text-gray-700">
              <li>Talking about wanting to die or feeling hopeless</li>
              <li>Feeling like a burden to others</li>
              <li>Increasing use of alcohol or drugs</li>
              <li>Withdrawing from friends and family</li>
              <li>Giving away possessions</li>
              <li>Sleeping too much or too little</li>
              <li>Acting agitated or reckless</li>
            </ul>

            <h3 className="text-lg font-medium text-gray-900 mt-6">What You Can Do</h3>
            <ul className="text-gray-700">
              <li><strong>Ask directly:</strong> "Are you thinking about suicide?" This won't plant the idea.</li>
              <li><strong>Listen without judgment:</strong> Let them share their feelings.</li>
              <li><strong>Stay with them:</strong> Don't leave someone in crisis alone.</li>
              <li><strong>Help them connect:</strong> Offer to call the Crisis Line together.</li>
              <li><strong>Remove access to lethal means:</strong> Safely store firearms and medications.</li>
            </ul>

            <div className="bg-blue-50 p-4 rounded-lg mt-6">
              <p className="text-blue-800 font-medium">
                You don't have to have all the answers. Just being there matters.
              </p>
            </div>
          </div>
        </section>

        {/* Footer Note */}
        <div className="text-center text-gray-500 text-sm">
          <p>
            VetAssist is not a crisis service. If you are in immediate danger, call 911.
          </p>
          <p className="mt-2">
            Resources last verified: February 2026
          </p>
        </div>
      </div>
    </main>
  )
}

interface ResourceCardProps {
  title: string
  description: string
  link: string
  phone?: string
}

function ResourceCard({ title, description, link, phone }: ResourceCardProps) {
  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
      <h3 className="font-medium text-gray-900">{title}</h3>
      <p className="text-sm text-gray-600 mt-1">{description}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <a
          href={link}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-blue-600 hover:text-blue-800 underline"
        >
          Visit Website
        </a>
        {phone && (
          <a
            href={`tel:${phone.replace(/\D/g, '')}`}
            className="text-sm text-blue-600 hover:text-blue-800 underline"
          >
            {phone}
          </a>
        )}
      </div>
    </div>
  )
}
```

### 2. Update Navigation

**Path:** `/ganuda/vetassist/frontend/components/Navigation.tsx` (or similar nav component)

Add a nav item for the crisis resources page:

```tsx
// Add to navigation items array
{
  name: 'Crisis Resources',
  href: '/crisis-resources',
  icon: HeartIcon, // or appropriate icon
  className: 'text-red-600 hover:text-red-800', // Make it stand out subtly
}
```

**Alternative:** If using a header component, add:

```tsx
<Link
  href="/crisis-resources"
  className="text-red-600 hover:text-red-800 font-medium"
>
  Get Help
</Link>
```

---

## Verification Checklist

- [ ] Page loads at `/crisis-resources`
- [ ] Veterans Crisis Line 988 link works (call intent)
- [ ] Text 838255 link works (SMS intent)
- [ ] Chat link opens VeteransCrisisLine.net
- [ ] All external links open in new tab
- [ ] Navigation tab visible in main nav
- [ ] Page is mobile-responsive
- [ ] Page is screen-reader accessible
- [ ] Native veteran resources section included
- [ ] "Helping a Veteran in Crisis" section included

---

## Accessibility Requirements

- [ ] All links have descriptive text
- [ ] Color contrast meets WCAG AA
- [ ] Page works with keyboard navigation only
- [ ] Phone links use `tel:` protocol
- [ ] SMS links use `sms:` protocol

---

## Maintenance Notes

- **Quarterly:** Verify all external links still work
- **Annually:** Review and update resource list
- **On VA update:** Check if any phone numbers or URLs changed

---

## No Backend Required

This is a static content page. No API endpoints, database tables, or backend changes needed.

---

## Related Documents

- Ultrathink: ULTRATHINK-VETASSIST-PHASE1-ENHANCEMENTS-FEB06-2026.md
- Council Vote: Audit hash 0cc1c5d0138a8d6d

---

*For Seven Generations*
