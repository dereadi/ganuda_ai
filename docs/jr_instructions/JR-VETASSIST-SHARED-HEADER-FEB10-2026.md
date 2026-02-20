# Jr Instruction: VetAssist Shared Header Enhancement

**ID:** JR-VETASSIST-SHARED-HEADER-FEB10-2026
**Kanban:** #1727 (also addresses #1721 - mobile hamburger menu)
**Priority:** P2
**Estimated Effort:** 2-3 hours
**Assigned Node:** SE Jr (any)

---

## Objective

Enhance the existing shared Header component (`/ganuda/vetassist/frontend/components/Header.tsx`) with improved navigation structure, Dashboard link for authenticated users, accessible mobile hamburger menu with slide-down animation, and proper ARIA attributes. Also deprecate the standalone `MobileNav.tsx` component which duplicates header functionality.

---

## Context

- The Header component already exists and is rendered in the root layout (`app/layout.tsx`). It already has desktop nav, mobile hamburger toggle, auth-aware sign in/out, and active-page highlighting.
- A separate `MobileNav.tsx` component exists but is NOT used anywhere (the Header handles its own mobile menu). We will leave it in place but add a deprecation comment.
- The current Header is functional but has these gaps:
  1. No "Dashboard" link for logged-in users (they can only reach it via redirect from Home)
  2. Mobile menu has no transition animation (just appears/disappears)
  3. Mobile menu does not show Dashboard or Settings links for authenticated users
  4. No skip-to-content link for accessibility
  5. The nav items array is not conditional on auth state
- The `useAuth` hook from `@/lib/auth-context` provides `{ user, loading, logout }`.
- The app uses `lucide-react` for icons (`Shield`, `Menu`, `X` are already imported).

---

## Acceptance Criteria

1. Desktop nav shows: Home, Calculator, AI Chat, Resources, About (same as current)
2. When user is logged in, desktop nav adds a "Dashboard" link between Home and Calculator
3. Mobile hamburger menu opens with a CSS transition (max-height animation)
4. Mobile menu shows Dashboard, Settings, and Sign Out when authenticated
5. Mobile menu shows Sign In link when not authenticated
6. All interactive elements have proper ARIA labels
7. A visually-hidden "Skip to main content" link is added before the header nav
8. Header remains sticky at the top (`sticky top-0 z-50`)
9. `MobileNav.tsx` gets a deprecation comment at the top
10. No new files created (edits only)

---

## Implementation

### Step 1: Update Header Component

File: `/ganuda/vetassist/frontend/components/Header.tsx`

<<<<<<< SEARCH
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Shield, Menu, X } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '@/lib/auth-context';

const navItems = [
  { href: '/', label: 'Home' },
  { href: '/calculator', label: 'Calculator' },
  { href: '/chat', label: 'AI Chat' },
  { href: '/resources', label: 'Resources' },
  { href: '/about', label: 'About' },
];

const adminNavItems = [
  { href: '/admin', label: 'Admin' },
];

export default function Header() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, logout } = useAuth();
  const isLoggedIn = user !== null;

  return (
    <header className="border-b bg-white sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <Shield className="h-8 w-8 text-primary" />
            <span className="text-2xl font-bold">Ganuda VetAssist</span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-6">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`hover:text-primary transition ${
                  pathname === item.href ? 'text-primary font-semibold' : ''
                }`}
              >
                {item.label}
              </Link>
            ))}

            {/* Auth Section */}
            {isLoggedIn ? (
              <div className="flex items-center space-x-4 ml-4 pl-4 border-l">
                <span className="text-sm text-gray-600">
                  Hi, {user?.first_name || 'Veteran'}
                </span>
                <Link
                  href="/settings"
                  className="text-sm text-gray-600 hover:text-primary"
                >
                  Settings
                </Link>
                <button
                  onClick={logout}
                  className="text-sm text-gray-600 hover:text-primary"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <Link
                href="/login"
                className="ml-4 pl-4 border-l text-primary hover:text-primary/80 font-medium"
              >
                Sign In
              </Link>
            )}
          </nav>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? (
              <X className="h-6 w-6" />
            ) : (
              <Menu className="h-6 w-6" />
            )}
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <nav className="md:hidden mt-4 pb-4 border-t pt-4">
            <div className="flex flex-col space-y-3">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`py-2 ${
                    pathname === item.href ? 'text-primary font-semibold' : ''
                  }`}
                >
                  {item.label}
                </Link>
              ))}

              {isLoggedIn ? (
                <button
                  onClick={() => {
                    logout();
                    setMobileMenuOpen(false);
                  }}
                  className="py-2 text-left text-gray-600"
                >
                  Sign Out ({user?.first_name})
                </button>
              ) : (
                <Link
                  href="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="py-2 text-primary font-medium"
                >
                  Sign In
                </Link>
              )}
            </div>
          </nav>
        )}
      </div>
    </header>
  );
}
=======
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Shield, Menu, X, LayoutDashboard } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/lib/auth-context';

/** Public nav items shown to all visitors */
const publicNavItems = [
  { href: '/', label: 'Home' },
  { href: '/calculator', label: 'Calculator' },
  { href: '/chat', label: 'AI Chat' },
  { href: '/resources', label: 'Resources' },
  { href: '/about', label: 'About' },
];

/** Extra nav items shown only when logged in (inserted after Home) */
const authNavItems = [
  { href: '/dashboard', label: 'Dashboard' },
];

export default function Header() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const mobileMenuRef = useRef<HTMLDivElement>(null);
  const { user, logout } = useAuth();
  const isLoggedIn = user !== null;

  // Build nav items list: insert Dashboard after Home for logged-in users
  const navItems = isLoggedIn
    ? [
        publicNavItems[0],
        ...authNavItems,
        ...publicNavItems.slice(1),
      ]
    : publicNavItems;

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  // Close mobile menu on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && mobileMenuOpen) {
        setMobileMenuOpen(false);
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [mobileMenuOpen]);

  return (
    <>
      {/* Skip to main content link (accessibility) */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[60] focus:bg-primary focus:text-primary-foreground focus:px-4 focus:py-2 focus:rounded-md focus:text-sm focus:font-medium"
      >
        Skip to main content
      </a>

      <header className="border-b bg-white sticky top-0 z-50" role="banner">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link href="/" className="flex items-center space-x-2" aria-label="Ganuda VetAssist home">
              <Shield className="h-8 w-8 text-primary" aria-hidden="true" />
              <span className="text-2xl font-bold">Ganuda VetAssist</span>
            </Link>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-6" aria-label="Main navigation">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`hover:text-primary transition ${
                    pathname === item.href ? 'text-primary font-semibold' : 'text-foreground'
                  }`}
                  aria-current={pathname === item.href ? 'page' : undefined}
                >
                  {item.label}
                </Link>
              ))}

              {/* Auth Section */}
              {isLoggedIn ? (
                <div className="flex items-center space-x-4 ml-4 pl-4 border-l">
                  <span className="text-sm text-muted-foreground">
                    Hi, {user?.first_name || 'Veteran'}
                  </span>
                  <Link
                    href="/settings"
                    className="text-sm text-muted-foreground hover:text-primary transition"
                  >
                    Settings
                  </Link>
                  <button
                    onClick={logout}
                    className="text-sm text-muted-foreground hover:text-primary transition"
                  >
                    Sign Out
                  </button>
                </div>
              ) : (
                <Link
                  href="/login"
                  className="ml-4 pl-4 border-l text-primary hover:text-primary/80 font-medium transition"
                >
                  Sign In
                </Link>
              )}
            </nav>

            {/* Mobile Menu Button */}
            <button
              className="md:hidden p-2 rounded-md hover:bg-muted transition"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
              aria-expanded={mobileMenuOpen}
              aria-controls="mobile-nav-menu"
            >
              {mobileMenuOpen ? (
                <X className="h-6 w-6" aria-hidden="true" />
              ) : (
                <Menu className="h-6 w-6" aria-hidden="true" />
              )}
            </button>
          </div>

          {/* Mobile Navigation with slide-down transition */}
          <div
            id="mobile-nav-menu"
            ref={mobileMenuRef}
            className={`md:hidden overflow-hidden transition-all duration-300 ease-in-out ${
              mobileMenuOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
            }`}
            role="navigation"
            aria-label="Mobile navigation"
          >
            <div className="pt-4 pb-4 border-t mt-4">
              <div className="flex flex-col space-y-1">
                {navItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`py-3 px-3 rounded-md transition ${
                      pathname === item.href
                        ? 'text-primary font-semibold bg-primary/5'
                        : 'text-foreground hover:bg-muted'
                    }`}
                    aria-current={pathname === item.href ? 'page' : undefined}
                  >
                    {item.label}
                  </Link>
                ))}

                {/* Auth actions in mobile menu */}
                <div className="border-t mt-2 pt-2">
                  {isLoggedIn ? (
                    <>
                      <Link
                        href="/settings"
                        onClick={() => setMobileMenuOpen(false)}
                        className="block py-3 px-3 rounded-md text-muted-foreground hover:bg-muted transition"
                      >
                        Settings
                      </Link>
                      <button
                        onClick={() => {
                          logout();
                          setMobileMenuOpen(false);
                        }}
                        className="w-full text-left py-3 px-3 rounded-md text-muted-foreground hover:bg-muted transition"
                      >
                        Sign Out ({user?.first_name || 'Veteran'})
                      </button>
                    </>
                  ) : (
                    <Link
                      href="/login"
                      onClick={() => setMobileMenuOpen(false)}
                      className="block py-3 px-3 rounded-md text-primary font-medium hover:bg-primary/5 transition"
                    >
                      Sign In
                    </Link>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>
    </>
  );
}
>>>>>>> REPLACE

### Step 2: Add skip-link target to root layout

The skip-to-content link targets `#main-content`. The root layout's `<main>` tag needs the corresponding `id`.

File: `/ganuda/vetassist/frontend/app/layout.tsx`

<<<<<<< SEARCH
            <main className="flex-1">
=======
            <main id="main-content" className="flex-1">
>>>>>>> REPLACE

### Step 3: Deprecate standalone MobileNav component

File: `/ganuda/vetassist/frontend/components/MobileNav.tsx`

<<<<<<< SEARCH
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
=======
/**
 * @deprecated This component is no longer used. Mobile navigation is handled
 * directly inside components/Header.tsx. Kept for reference only.
 * Remove after Feb 28, 2026 if no imports reference it.
 */
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
>>>>>>> REPLACE

---

## Verification

After applying all edits:

1. Desktop: Verify the header shows Home, Calculator, AI Chat, Resources, About when logged out
2. Desktop: Log in and verify Dashboard appears between Home and Calculator
3. Mobile: Tap hamburger -- menu should slide down smoothly (300ms transition)
4. Mobile: Verify Dashboard, Settings, Sign Out appear when logged in
5. Mobile: Press Escape key -- menu should close
6. Accessibility: Tab to the page -- "Skip to main content" link should appear on focus
7. Accessibility: All nav links have `aria-current="page"` when active
8. Verify the app still builds without TypeScript errors

---

## Notes

- The `LayoutDashboard` icon is imported but not used in the nav items themselves (text-only links match the existing pattern). If a future ticket calls for icon-based nav, it is ready.
- The `max-h-96` (24rem) is sufficient for the mobile menu even with all auth links. If more items are added in the future, increase this value.
- The `MobileNav.tsx` deprecation comment preserves the file for reference. A future cleanup ticket can remove it.
