# Jr Instruction: VetAssist Shared Header Component

**Task ID:** VETASSIST-SHARED-HEADER
**Priority:** P1
**Date:** January 24, 2026
**Phase:** UX Foundation (1 of 3)

## Objective

Create a reusable Header component with consistent navigation across all pages.

## Files to Modify (2 files)

1. `/ganuda/vetassist/frontend/components/Header.tsx` (create)
2. `/ganuda/vetassist/frontend/app/layout.tsx`

## Required Changes

### 1. Header.tsx - Create component

Create `/ganuda/vetassist/frontend/components/Header.tsx`:

```typescript
'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';

interface User {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
}

export default function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('vetassist_token');
    if (token) {
      // Fetch user data
      fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(res => res.ok ? res.json() : null)
      .then(data => setUser(data))
      .catch(() => setUser(null));
    }
  }, [pathname]);

  const handleLogout = async () => {
    const token = localStorage.getItem('vetassist_token');
    if (token) {
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
    }
    localStorage.removeItem('vetassist_token');
    setUser(null);
    router.push('/');
  };

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

  return (
    <header className="bg-blue-900 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <span className="text-2xl font-bold">VetAssist</span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-4">
            {[...navLinks, ...authLinks].map(link => (
              <Link
                key={link.href}
                href={link.href}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors
                  ${isActive(link.href)
                    ? 'bg-blue-700 text-white'
                    : 'text-blue-100 hover:bg-blue-800 hover:text-white'
                  }`}
              >
                {link.label}
              </Link>
            ))}

            {/* Auth buttons */}
            {user ? (
              <div className="flex items-center space-x-2 ml-4">
                <span className="text-sm text-blue-200">
                  {user.first_name || user.email}
                </span>
                <button
                  onClick={handleLogout}
                  className="px-3 py-2 rounded-md text-sm font-medium bg-red-600 hover:bg-red-700"
                >
                  Logout
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2 ml-4">
                <Link
                  href="/login"
                  className="px-3 py-2 rounded-md text-sm font-medium text-blue-100 hover:text-white"
                >
                  Login
                </Link>
                <Link
                  href="/register"
                  className="px-4 py-2 rounded-md text-sm font-medium bg-green-600 hover:bg-green-700"
                >
                  Sign Up
                </Link>
              </div>
            )}
          </nav>

          {/* Mobile menu button */}
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="md:hidden p-2 rounded-md text-blue-200 hover:text-white hover:bg-blue-800"
            aria-label="Toggle menu"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {isMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile menu will be added in MobileNav task */}
      </div>
    </header>
  );
}
```

### 2. layout.tsx - Integrate Header

Update `/ganuda/vetassist/frontend/app/layout.tsx`:

```typescript
import Header from '@/components/Header';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Header />
        <main>{children}</main>
      </body>
    </html>
  );
}
```

## Output

Generate both files completely.

## Success Criteria

- [ ] Header component created with navigation links
- [ ] Header shows different links for authenticated vs unauthenticated users
- [ ] Header integrated into root layout
- [ ] Mobile menu button visible (functionality in next task)
