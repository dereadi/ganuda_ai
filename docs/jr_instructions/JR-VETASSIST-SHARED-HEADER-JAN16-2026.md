# JR Instruction: VetAssist Shared Header Component

## Metadata
```yaml
task_id: vetassist_shared_header
priority: 1
assigned_to: Code Jr.
target: frontend
```

## Problem

Each page has its own header/nav with inconsistent links:
- Home: Calculator, AI Chat, Resources, About
- Calculator: Calculator, AI Chat, Resources (missing About)
- Other pages vary

No Sign In/Sign Out functionality in nav.

## Solution

### Task 1: Create Shared Header Component

Create `/ganuda/vetassist/frontend/components/Header.tsx`:

```typescript
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Shield, Menu, X } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '@/lib/auth-context';

const navItems = [
  { href: '/calculator', label: 'Calculator' },
  { href: '/chat', label: 'AI Chat' },
  { href: '/resources', label: 'Resources' },
  { href: '/about', label: 'About' },
];

export default function Header() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, isAuthenticated, logout } = useAuth();

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
            {isAuthenticated ? (
              <div className="flex items-center space-x-4 ml-4 pl-4 border-l">
                <span className="text-sm text-gray-600">
                  Hi, {user?.first_name || 'Veteran'}
                </span>
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

              {isAuthenticated ? (
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
```

### Task 2: Update Layout to Include Header

Edit `/ganuda/vetassist/frontend/app/layout.tsx`:

```typescript
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import Header from "@/components/Header";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Ganuda VetAssist | AI-Powered VA Claims Assistance",
  description: "Free AI-powered assistance for U.S. veterans navigating VA disability claims.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <div className="min-h-screen flex flex-col">
            <Header />
            <main className="flex-1">
              {children}
            </main>
          </div>
        </AuthProvider>
        <footer className="border-t mt-auto">
          <div className="container mx-auto px-4 py-6 text-center text-sm text-muted-foreground">
            <p>Ganuda VetAssist Platform | For the Seven Generations</p>
            <p className="mt-1">Educational tool only. Not legal advice. Platform: Bluefin</p>
          </div>
        </footer>
      </body>
    </html>
  );
}
```

### Task 3: Remove Duplicate Headers from Pages

Remove the `<header>` sections from:
- `/app/page.tsx` (lines 8-23)
- `/app/calculator/page.tsx` (lines 113-133)
- `/app/chat/page.tsx` (find and remove)
- `/app/resources/page.tsx` (find and remove)
- Any other pages with duplicate headers

### Task 4: Fix Page Structure

Each page should now just have its content, not the header:

```typescript
// Example: page.tsx
export default function HomePage() {
  return (
    <>
      {/* Hero Section - no header needed */}
      <section className="bg-gradient-to-b from-primary/10 to-background py-20">
        {/* content */}
      </section>
      {/* rest of page */}
    </>
  );
}
```

## Verification

1. All pages should have identical header
2. Current page should be highlighted in nav
3. Sign In shows when logged out
4. User name + Sign Out shows when logged in
5. Mobile hamburger menu works on all pages
6. About link present on all pages

---

*Cherokee AI Federation - For the Seven Generations*
