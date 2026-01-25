# Jr Instruction: VetAssist Mobile Navigation

**Task ID:** VETASSIST-MOBILE-NAV
**Priority:** P2
**Date:** January 24, 2026
**Phase:** UX Foundation (2 of 3)

## Objective

Add mobile-friendly navigation with hamburger menu and slide-out drawer.

## Files to Modify (2 files)

1. `/ganuda/vetassist/frontend/components/MobileNav.tsx` (create)
2. `/ganuda/vetassist/frontend/components/Header.tsx` (update)

## Required Changes

### 1. MobileNav.tsx - Create mobile navigation drawer

Create `/ganuda/vetassist/frontend/components/MobileNav.tsx`:

```typescript
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface MobileNavProps {
  isOpen: boolean;
  onClose: () => void;
  user: { email: string; first_name?: string } | null;
  onLogout: () => void;
}

export default function MobileNav({ isOpen, onClose, user, onLogout }: MobileNavProps) {
  const pathname = usePathname();

  const navLinks = [
    { href: '/', label: 'Home' },
    { href: '/about', label: 'About' },
    { href: '/calculator', label: 'Calculator' },
    { href: '/chat', label: 'Chat' },
  ];

  const authLinks = user ? [
    { href: '/dashboard', label: 'Dashboard' },
    { href: '/wizard', label: 'Start Claim' },
  ] : [];

  const isActive = (href: string) => pathname === href;

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Slide-out drawer */}
      <div
        className={`fixed top-0 right-0 h-full w-64 bg-blue-900 z-50 transform transition-transform duration-300 ease-in-out md:hidden ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Close button */}
        <div className="flex justify-end p-4">
          <button
            onClick={onClose}
            className="p-2 text-blue-200 hover:text-white"
            aria-label="Close menu"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* User info if logged in */}
        {user && (
          <div className="px-4 py-3 border-b border-blue-800">
            <p className="text-sm text-blue-200">Logged in as</p>
            <p className="text-white font-medium truncate">
              {user.first_name || user.email}
            </p>
          </div>
        )}

        {/* Navigation links */}
        <nav className="py-4">
          {[...navLinks, ...authLinks].map(link => (
            <Link
              key={link.href}
              href={link.href}
              onClick={onClose}
              className={`block px-6 py-3 text-base font-medium transition-colors ${
                isActive(link.href)
                  ? 'bg-blue-700 text-white'
                  : 'text-blue-100 hover:bg-blue-800 hover:text-white'
              }`}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        {/* Auth buttons */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-blue-800">
          {user ? (
            <button
              onClick={() => {
                onLogout();
                onClose();
              }}
              className="w-full px-4 py-3 text-center rounded-md bg-red-600 text-white font-medium hover:bg-red-700"
            >
              Logout
            </button>
          ) : (
            <div className="space-y-2">
              <Link
                href="/login"
                onClick={onClose}
                className="block w-full px-4 py-3 text-center rounded-md border border-blue-400 text-blue-100 font-medium hover:bg-blue-800"
              >
                Login
              </Link>
              <Link
                href="/register"
                onClick={onClose}
                className="block w-full px-4 py-3 text-center rounded-md bg-green-600 text-white font-medium hover:bg-green-700"
              >
                Sign Up Free
              </Link>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
```

### 2. Header.tsx - Integrate MobileNav

Update `/ganuda/vetassist/frontend/components/Header.tsx` to include MobileNav:

Add import at top:
```typescript
import MobileNav from './MobileNav';
```

Add MobileNav component before closing `</header>`:
```typescript
{/* Mobile Navigation Drawer */}
<MobileNav
  isOpen={isMenuOpen}
  onClose={() => setIsMenuOpen(false)}
  user={user}
  onLogout={handleLogout}
/>
```

## Output

Generate both files completely.

## Success Criteria

- [ ] MobileNav component created with slide-out drawer
- [ ] Header updated to use MobileNav
- [ ] Navigation works on mobile devices
- [ ] Drawer closes when clicking outside or on link
