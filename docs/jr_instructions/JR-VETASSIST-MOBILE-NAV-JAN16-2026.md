# JR Instruction: VetAssist Mobile Navigation

## Metadata
```yaml
task_id: vetassist_mobile_nav
priority: 2
ticket_id: 1721
assigned_to: Code Jr.
target: frontend
```

## Problem

Navigation is hidden on mobile (md breakpoint) with no hamburger menu. Many veterans access via phone.

## Solution

### Task 1: Create Mobile Nav Component

Create `/ganuda/vetassist/frontend/components/MobileNav.tsx`:

```typescript
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navItems = [
  { href: '/', label: 'Home' },
  { href: '/calculator', label: 'Calculator' },
  { href: '/chat', label: 'Chat' },
  { href: '/resources', label: 'Resources' },
  { href: '/about', label: 'About' },
];

export default function MobileNav() {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();

  return (
    <div className="md:hidden">
      {/* Hamburger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 text-gray-600 hover:text-gray-900"
        aria-label="Toggle menu"
      >
        {isOpen ? (
          // X icon
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          // Hamburger icon
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        )}
      </button>

      {/* Mobile Menu Dropdown */}
      {isOpen && (
        <div className="absolute top-16 left-0 right-0 bg-white shadow-lg border-t z-50">
          <nav className="flex flex-col">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setIsOpen(false)}
                className={`px-4 py-3 border-b text-lg ${
                  pathname === item.href
                    ? 'bg-blue-50 text-blue-800 font-medium'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                {item.label}
              </Link>
            ))}
            <div className="p-4 border-t">
              <Link
                href="/login"
                onClick={() => setIsOpen(false)}
                className="block w-full text-center py-2 px-4 bg-blue-800 text-white rounded hover:bg-blue-900"
              >
                Sign In
              </Link>
            </div>
          </nav>
        </div>
      )}
    </div>
  );
}
```

### Task 2: Update Header/Layout

In the main layout or header component, add the mobile nav:

```typescript
import MobileNav from '@/components/MobileNav';

// In the header section:
<header className="bg-white shadow-sm sticky top-0 z-40">
  <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
    <Link href="/" className="text-xl font-bold text-blue-800">
      VetAssist
    </Link>

    {/* Desktop Navigation - hidden on mobile */}
    <nav className="hidden md:flex items-center gap-6">
      {/* existing nav items */}
    </nav>

    {/* Mobile Navigation - visible only on mobile */}
    <MobileNav />
  </div>
</header>
```

### Task 3: Ensure Proper Z-Index

Add to global CSS if needed:

```css
/* Ensure mobile menu appears above content */
.mobile-nav-overlay {
  z-index: 50;
}
```

## Verification

1. View site on mobile viewport (< 768px)
2. Hamburger icon should appear
3. Clicking opens full-width dropdown menu
4. Current page should be highlighted
5. Clicking a link closes menu and navigates
6. Menu should not overlap with page content awkwardly

---

*Cherokee AI Federation - For the Seven Generations*
