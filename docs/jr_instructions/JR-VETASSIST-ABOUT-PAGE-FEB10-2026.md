# Jr Instruction: VetAssist About Page Enhancement

**ID:** JR-VETASSIST-ABOUT-PAGE-FEB10-2026
**Kanban:** #1720
**Priority:** P2
**Estimated Effort:** 1-2 hours
**Assigned Node:** SE Jr (any)

---

## Objective

Replace the existing bare-bones About page with a polished, branded page that communicates VetAssist's mission, Cherokee AI Federation identity, the 7-specialist Council architecture, and a clear educational-tool disclaimer. The current page uses hardcoded gray/blue colors instead of the design-system CSS variables used everywhere else.

---

## Context

- The About page already exists at `/ganuda/vetassist/frontend/app/about/page.tsx`.
- The rest of the site uses Tailwind CSS variables (`text-primary`, `bg-muted`, `text-muted-foreground`, etc.) defined in `globals.css`. The current About page uses raw `bg-gray-50`, `text-blue-800`, etc., which is inconsistent.
- The page is a Server Component (no `'use client'`), which is correct -- keep it that way.
- The Header and Footer are rendered by the root layout (`app/layout.tsx`), so the About page should NOT include its own header/footer.
- lucide-react icons are available throughout the project (see calculator page, chat page).

---

## Acceptance Criteria

1. About page uses the app's CSS variable classes (`text-primary`, `bg-card`, `text-muted-foreground`, etc.) instead of hardcoded Tailwind colors
2. Includes sections: Mission, How It Works (7-specialist Council), Features, Disclaimer, Cherokee AI Federation identity
3. Has a "For the Seven Generations" tagline
4. CTA buttons link to /calculator and /chat
5. Page metadata has proper title and description
6. Page is accessible (semantic headings, good contrast, proper alt text)
7. No `'use client'` directive -- remains a Server Component

---

## Implementation

File: `/ganuda/vetassist/frontend/app/about/page.tsx`

Replace the entire file contents with the following:

<<<<<<< SEARCH
import Link from 'next/link';

export const metadata = {
  title: 'About VetAssist | Cherokee AI Federation',
  description: 'Learn about VetAssist - AI-powered assistance for veterans navigating VA disability claims.',
};

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* Header */}
        <h1 className="text-4xl font-bold text-gray-900 mb-6">
          About VetAssist
        </h1>

        {/* Mission */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">Our Mission</h2>
          <p className="text-lg text-gray-600 mb-4">
            VetAssist is an AI-powered platform designed to help veterans understand
            and navigate the VA disability claims process. We provide educational
            resources, a disability rating calculator, and an AI assistant trained
            on VA regulations.
          </p>
          <p className="text-lg text-gray-600">
            Built by the Cherokee AI Federation, VetAssist embodies the principle of
            serving the Seven Generations - creating technology that benefits our
            veterans today and preserves knowledge for those who serve tomorrow.
          </p>
        </section>

        {/* Features */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">Features</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-xl font-medium text-blue-800 mb-2">
                VA Disability Calculator
              </h3>
              <p className="text-gray-600">
                Calculate your combined disability rating using the official
                VA formula (38 CFR 4.25), including bilateral factor and
                special monthly compensation.
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-xl font-medium text-blue-800 mb-2">
                AI Assistant
              </h3>
              <p className="text-gray-600">
                Ask questions about VA claims, regulations, and processes.
                Our 7-specialist AI council provides balanced, cited responses.
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-xl font-medium text-blue-800 mb-2">
                Educational Resources
              </h3>
              <p className="text-gray-600">
                Access guides, articles, and explanations about the VA
                disability system, from beginner basics to advanced topics.
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-xl font-medium text-blue-800 mb-2">
                Privacy Protected
              </h3>
              <p className="text-gray-600">
                Your personal information is automatically detected and
                redacted. We never store your SSN, VA file number, or
                other sensitive data.
              </p>
            </div>
          </div>
        </section>

        {/* Disclaimer */}
        <section className="mb-12 bg-amber-50 border border-amber-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-amber-800 mb-3">
            Important Disclaimer
          </h2>
          <p className="text-amber-900">
            VetAssist provides <strong>educational information only</strong>.
            This is not legal advice, and we are not a Veterans Service
            Organization (VSO). For official claims assistance, please contact
            an accredited VSO, attorney, or claims agent. The VA's official
            website is <a href="https://www.va.gov" className="underline">va.gov</a>.
          </p>
        </section>

        {/* Cherokee AI Federation */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            Cherokee AI Federation
          </h2>
          <p className="text-lg text-gray-600 mb-4">
            VetAssist is built by the Cherokee AI Federation, a collective
            developing AI systems guided by indigenous wisdom and the principle
            of thinking seven generations ahead.
          </p>
          <p className="text-gray-600 italic">
            "For the Seven Generations"
          </p>
        </section>

        {/* CTA */}
        <div className="flex gap-4">
          <Link
            href="/calculator"
            className="px-6 py-3 bg-blue-800 text-white rounded-lg hover:bg-blue-900 transition"
          >
            Try the Calculator
          </Link>
          <Link
            href="/chat"
            className="px-6 py-3 border border-blue-800 text-blue-800 rounded-lg hover:bg-blue-50 transition"
          >
            Ask a Question
          </Link>
        </div>
      </div>
    </div>
  );
}
=======
import Link from 'next/link';
import type { Metadata } from 'next';
import { Shield, Calculator, MessageCircle, BookOpen, Lock, Users, Heart, Feather } from 'lucide-react';

export const metadata: Metadata = {
  title: 'About VetAssist | Cherokee AI Federation',
  description:
    'VetAssist is an AI-powered veteran benefits assistance platform built by the Cherokee AI Federation. Free for all U.S. veterans.',
};

export default function AboutPage() {
  return (
    <div className="bg-background">
      {/* Hero Section */}
      <section className="bg-gradient-to-b from-primary/10 to-background py-16">
        <div className="container mx-auto px-4 text-center max-w-3xl">
          <div className="inline-flex items-center justify-center p-3 bg-primary/10 rounded-full mb-6">
            <Shield className="h-10 w-10 text-primary" />
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">About VetAssist</h1>
          <p className="text-xl text-muted-foreground">
            AI-powered assistance helping U.S. veterans understand and navigate
            the VA disability claims process — free, forever.
          </p>
        </div>
      </section>

      <div className="container mx-auto px-4 py-12 max-w-4xl">
        {/* Mission */}
        <section className="mb-16">
          <h2 className="text-3xl font-bold mb-6">Our Mission</h2>
          <div className="space-y-4 text-lg text-muted-foreground">
            <p>
              Millions of U.S. veterans are entitled to disability compensation but
              struggle with a complex, opaque claims process. VetAssist exists to
              change that. We provide free, AI-powered educational tools so every
              veteran can understand their benefits and file with confidence.
            </p>
            <p>
              Built by the Cherokee AI Federation, VetAssist is guided by the
              principle of thinking seven generations ahead — creating technology
              that serves veterans today and preserves institutional knowledge for
              those who serve tomorrow.
            </p>
          </div>
        </section>

        {/* How It Works - Council */}
        <section className="mb-16">
          <h2 className="text-3xl font-bold mb-6">How It Works</h2>
          <div className="bg-card border rounded-lg p-6 mb-6">
            <div className="flex items-start gap-4">
              <Users className="h-8 w-8 text-primary flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-xl font-semibold mb-2">7-Specialist AI Council</h3>
                <p className="text-muted-foreground mb-4">
                  Unlike generic AI chatbots (which have a 56% citation error rate on
                  VA questions), VetAssist uses a council of seven specialized AI
                  agents. Each specialist reviews your question from a different
                  angle — regulations, medical evidence, legal precedent, appeals
                  strategy, and more — then they deliberate and deliver a single,
                  validated response with citations.
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                  <div className="bg-muted rounded-md p-2 text-center font-medium">Raven</div>
                  <div className="bg-muted rounded-md p-2 text-center font-medium">Turtle</div>
                  <div className="bg-muted rounded-md p-2 text-center font-medium">Peace Chief</div>
                  <div className="bg-muted rounded-md p-2 text-center font-medium">Crawdad</div>
                  <div className="bg-muted rounded-md p-2 text-center font-medium">Gecko</div>
                  <div className="bg-muted rounded-md p-2 text-center font-medium">Spider</div>
                  <div className="bg-muted rounded-md p-2 text-center font-medium">Eagle Eye</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="mb-16">
          <h2 className="text-3xl font-bold mb-6">Features</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <FeatureCard
              icon={<Calculator className="h-8 w-8 text-primary" />}
              title="VA Disability Calculator"
              description="Calculate your combined disability rating using the official VA formula (38 CFR 4.25), including bilateral factor and special monthly compensation."
            />
            <FeatureCard
              icon={<MessageCircle className="h-8 w-8 text-primary" />}
              title="AI Chat Assistant"
              description="Ask questions about VA claims, regulations, and processes. Every response is validated by the 7-specialist Council with regulatory citations."
            />
            <FeatureCard
              icon={<BookOpen className="h-8 w-8 text-primary" />}
              title="Educational Resources"
              description="Access guides, articles, and explanations about the VA disability system — from beginner basics to advanced topics like secondary conditions."
            />
            <FeatureCard
              icon={<Lock className="h-8 w-8 text-primary" />}
              title="Privacy Protected"
              description="Your personal information is automatically detected and redacted. We never store your SSN, VA file number, or other sensitive data."
            />
          </div>
        </section>

        {/* Disclaimer */}
        <section className="mb-16">
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-amber-800 mb-3">
              Important Disclaimer
            </h2>
            <p className="text-amber-900">
              VetAssist provides <strong>educational information only</strong>. This
              is not legal advice, and we are not a Veterans Service Organization
              (VSO). For official claims assistance, please contact an accredited
              VSO, attorney, or claims agent. The VA&apos;s official website is{' '}
              <a
                href="https://www.va.gov"
                className="underline font-medium"
                target="_blank"
                rel="noopener noreferrer"
              >
                va.gov
              </a>.
            </p>
          </div>
        </section>

        {/* Cherokee AI Federation */}
        <section className="mb-16">
          <div className="bg-gradient-to-br from-primary/5 to-primary/10 border border-primary/20 rounded-lg p-8 text-center">
            <Feather className="h-10 w-10 text-primary mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-4">Cherokee AI Federation</h2>
            <p className="text-muted-foreground mb-4 max-w-2xl mx-auto">
              VetAssist is built by the Cherokee AI Federation — a distributed
              collective developing AI systems guided by indigenous wisdom and the
              ethic of serving those who cannot yet speak for themselves.
            </p>
            <p className="text-lg font-semibold text-primary italic">
              &ldquo;For the Seven Generations&rdquo;
            </p>
          </div>
        </section>

        {/* CTA */}
        <section className="text-center pb-8">
          <h2 className="text-2xl font-bold mb-6">Ready to Get Started?</h2>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/calculator"
              className="inline-flex items-center justify-center px-8 py-3 bg-primary text-primary-foreground rounded-lg font-semibold hover:bg-primary/90 transition"
            >
              <Calculator className="mr-2 h-5 w-5" />
              Try the Calculator
            </Link>
            <Link
              href="/chat"
              className="inline-flex items-center justify-center px-8 py-3 border-2 border-primary text-primary rounded-lg font-semibold hover:bg-primary/10 transition"
            >
              <MessageCircle className="mr-2 h-5 w-5" />
              Ask a Question
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="bg-card border rounded-lg p-6 hover:shadow-lg transition">
      <div className="mb-3">{icon}</div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-muted-foreground">{description}</p>
    </div>
  );
}
>>>>>>> REPLACE

---

## Verification

After applying the edit, visually confirm:

- Page renders at `/about` without errors
- All sections are present: Mission, How It Works, Features, Disclaimer, Cherokee AI Federation, CTA
- Styling uses CSS variable tokens (inspect elements -- should see `hsl(var(--primary))` etc.)
- CTA buttons navigate to /calculator and /chat
- Mobile layout stacks the feature cards into a single column
- No `'use client'` banner appears in the file

---

## Notes

- The `Feather` icon from lucide-react is used for the Cherokee AI Federation branding section. If lucide-react does not ship a `Feather` icon in the installed version, fall back to `Shield`.
- The 7 specialist names (Raven, Turtle, Peace Chief, Crawdad, Gecko, Spider, Eagle Eye) match the council configuration in `specialist_council.py`.
