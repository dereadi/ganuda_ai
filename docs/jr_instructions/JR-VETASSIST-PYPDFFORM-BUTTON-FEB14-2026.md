# Jr Instruction: VetAssist — Add FormGenerator Button to Wizard Completion

**Kanban**: #1749
**Story Points**: 3
**Priority**: 21 (RC-2026-02A — last item, closes the sprint)
**Risk**: LOW — frontend-only, adds button to existing grid

## Objective

The PyPDFForm backend (form_generator.py), API endpoint (/api/v1/forms/generate),
and FormGenerator React component are ALL done. The only missing piece is wiring
the button into the wizard completion page.

## Step 1: Add FormGenerator import and button to completion page

File: `/ganuda/vetassist/frontend/app/wizard/[sessionId]/complete/page.tsx`

```
<<<<<<< SEARCH
import { FileText, Printer, MessageSquare, Home } from 'lucide-react';
=======
import { FileText, Printer, MessageSquare, Home, ClipboardList } from 'lucide-react';
import { FormGenerator } from '@/components/FormGenerator';
>>>>>>> REPLACE
```

## Step 2: Add Generate VA Forms button to the actions grid

File: `/ganuda/vetassist/frontend/app/wizard/[sessionId]/complete/page.tsx`

```
<<<<<<< SEARCH
            <button
              onClick={() => router.push('/dashboard')}
              className="flex items-center gap-2 px-4 py-3 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              <Home className="w-5 h-5" />
              <span>Back to Dashboard</span>
            </button>
=======
            <button
              onClick={() => router.push('/dashboard')}
              className="flex items-center gap-2 px-4 py-3 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              <Home className="w-5 h-5" />
              <span>Back to Dashboard</span>
            </button>
            <button
              onClick={() => setShowFormGenerator(true)}
              className="flex items-center gap-2 px-4 py-3 bg-green-100 hover:bg-green-200 text-green-800 rounded-lg transition-colors"
            >
              <ClipboardList className="w-5 h-5" />
              <span>Generate VA Forms</span>
            </button>
>>>>>>> REPLACE
```

## Step 3: Add state and FormGenerator modal

File: `/ganuda/vetassist/frontend/app/wizard/[sessionId]/complete/page.tsx`

```
<<<<<<< SEARCH
  const router = useRouter();
=======
  const router = useRouter();
  const [showFormGenerator, setShowFormGenerator] = useState(false);
>>>>>>> REPLACE
```

## Step 4: Add FormGenerator component render

File: `/ganuda/vetassist/frontend/app/wizard/[sessionId]/complete/page.tsx`

```
<<<<<<< SEARCH
    </div>
  );
}
=======
      {showFormGenerator && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Generate VA Forms</h3>
              <button onClick={() => setShowFormGenerator(false)} className="text-gray-500 hover:text-gray-700">✕</button>
            </div>
            <FormGenerator sessionId={params.sessionId} />
          </div>
        </div>
      )}
    </div>
  );
}
>>>>>>> REPLACE
```

## Manual Steps

On redfin, rebuild the VetAssist frontend:
```text
cd /ganuda/vetassist/frontend && npm run build
sudo systemctl restart vetassist-frontend
```
