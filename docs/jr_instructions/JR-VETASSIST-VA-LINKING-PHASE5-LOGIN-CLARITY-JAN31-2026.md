# JR-VETASSIST-VA-LINKING-PHASE5-LOGIN-CLARITY-JAN31-2026

## Metadata
- **Priority:** P2
- **Jr Type:** Engineering
- **Target Node:** sasass2 (192.168.132.200)
- **Category:** VetAssist — VA Account Linking Phase 5 (Login Page Clarity)
- **Depends On:** None (independent)
- **Council Vote:** ULTRATHINK-EXECUTOR-SEARCH-REPLACE-ARCHITECTURE-JAN31-2026

## Objective

Add a visible callout to the login page making it clear that veterans do NOT need a VA.gov account to get started. They can register with email/password and link VA.gov later.

## Step 1: Add "New to VetAssist?" Callout

**File:** `/ganuda/vetassist/frontend/app/(auth)/login/page.tsx`

<<<<<<< SEARCH
        <div className="text-center text-xs text-gray-500 mt-4">
          <p>Free for U.S. Veterans | For the Seven Generations</p>
        </div>
      </div>
    </div>
=======
        {/* New to VetAssist callout */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mt-4">
          <p className="text-sm font-medium text-green-800">
            New to VetAssist?
          </p>
          <p className="text-sm text-green-700 mt-1">
            You don&apos;t need a VA.gov account to get started.{' '}
            <Link href="/register" className="font-medium text-green-800 underline hover:text-green-900">
              Create a free account
            </Link>{' '}
            and explore your benefits. You can link your VA.gov account later from Settings.
          </p>
        </div>

        <div className="text-center text-xs text-gray-500 mt-4">
          <p>Free for U.S. Veterans | For the Seven Generations</p>
        </div>
      </div>
    </div>
>>>>>>> REPLACE

## Verification

The callout should appear between the VA.gov login button section and the footer text on the login page.

## Rollback

To undo, restore from search-replace backup:
  ls -la /ganuda/vetassist/frontend/app/\(auth\)/login/page.tsx.sr_backup_*
Restore the most recent backup.
