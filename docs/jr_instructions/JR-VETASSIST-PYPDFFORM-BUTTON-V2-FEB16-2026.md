# Jr Instruction: VetAssist PyPDFForm Button on Wizard Completion (v2)

**Kanban**: #1749 (3 SP)
**Council Vote**: #4d0745c25d7868c3 (PROCEED WITH CAUTION, 0.739)
**Sprint**: RC-2026-02A
**Assigned Jr**: Software Engineer Jr.
**Previous Attempt**: Jr #749 (failed — SEARCH blocks assumed `<button>` elements but actual code uses Next.js `<Link>` components)

## Context

VetAssist PyPDFForm integration is 95% complete. Backend endpoint (`/api/v1/forms/generate`) is LIVE. `FormGenerator.tsx` component is BUILT. Only remaining work: add a "Generate VA Forms" button to the wizard completion page that toggles the FormGenerator modal.

## Step 1: Add ClipboardList icon import

File: `/ganuda/vetassist/frontend/app/wizard/[sessionId]/complete/page.tsx`

<<<<<<< SEARCH
import {
  CheckCircle,
  Download,
  FileText,
  ArrowRight,
  Printer,
  Home,
  Loader2,
  Shield,
  Calendar,
  AlertCircle
} from 'lucide-react';
=======
import {
  CheckCircle,
  Download,
  FileText,
  ArrowRight,
  Printer,
  Home,
  Loader2,
  Shield,
  Calendar,
  AlertCircle,
  ClipboardList
} from 'lucide-react';
import FormGenerator from '@/components/FormGenerator';
>>>>>>> REPLACE

## Step 2: Add showFormGenerator state variable

File: `/ganuda/vetassist/frontend/app/wizard/[sessionId]/complete/page.tsx`

<<<<<<< SEARCH
  const [summary, setSummary] = useState<WizardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [completing, setCompleting] = useState(false);
=======
  const [summary, setSummary] = useState<WizardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [completing, setCompleting] = useState(false);
  const [showFormGenerator, setShowFormGenerator] = useState(false);
>>>>>>> REPLACE

## Step 3: Add Generate VA Forms button to the action grid

File: `/ganuda/vetassist/frontend/app/wizard/[sessionId]/complete/page.tsx`

<<<<<<< SEARCH
            <Link
              href="/dashboard"
              className="flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Home className="h-5 w-5" />
              <span>Back to Dashboard</span>
            </Link>
          </div>
        </div>
=======
            <button
              onClick={() => setShowFormGenerator(true)}
              className="flex items-center justify-center gap-2 px-4 py-3 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 transition-colors text-green-700"
            >
              <ClipboardList className="h-5 w-5" />
              <span>Generate VA Forms</span>
            </button>
            <Link
              href="/dashboard"
              className="flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Home className="h-5 w-5" />
              <span>Back to Dashboard</span>
            </Link>
          </div>
        </div>

        {/* Form Generator Modal */}
        {showFormGenerator && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Generate VA Forms</h2>
                <button
                  onClick={() => setShowFormGenerator(false)}
                  className="text-gray-400 hover:text-gray-600 text-xl"
                >
                  &times;
                </button>
              </div>
              <FormGenerator sessionId={sessionId} />
            </div>
          </div>
        )}
>>>>>>> REPLACE

## Verification

After deployment on **redfin**:

```text
cd /ganuda/vetassist/frontend && npm run build
```

Then navigate to a completed wizard session. The action grid should now show 5 buttons (Print, Download PDF, Ask AI, **Generate VA Forms**, Back to Dashboard). Clicking "Generate VA Forms" should open a modal with the FormGenerator component.

## Manual Steps (TPM only)

On **redfin**:
1. `cd /ganuda/vetassist/frontend && npm run build`
2. `sudo systemctl restart vetassist-frontend`
3. Test at http://192.168.132.223:3000/wizard/<any-session-id>/complete

## Rollback

Remove the ClipboardList import, FormGenerator import, showFormGenerator state, the button, and the modal block. Rebuild frontend.
