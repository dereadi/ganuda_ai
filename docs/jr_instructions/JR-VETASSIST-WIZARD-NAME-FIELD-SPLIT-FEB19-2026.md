# Jr Instruction: VetAssist Wizard Name Field Split

**Task**: Split single `full_name` field in 21-526EZ wizard Step 1 into `first_name`, `middle_initial`, `last_name`
**Priority**: 3 (HIGH — user-facing feedback from live testing)
**Source**: Meetup feedback from Joe (veteran user) and Maik, Feb 19 2026
**Assigned Jr**: Software Engineer Jr.

## Context

The VetAssist registration page already has `first_name` / `last_name` as separate fields in a grid layout. But the 21-526EZ wizard Step 1 ("Personal Information") still uses a single `full_name` field. This creates two problems:

1. **Data inconsistency**: Registration collects first/last, wizard collects full_name as one blob
2. **VA form mismatch**: The actual VA Form 21-526EZ has separate fields for first name, middle initial, and last name

The fix touches 4 files across frontend and backend.

## Step 1: Frontend — Split name field in wizard Step 1

File: `/ganuda/vetassist/frontend/app/wizard/[sessionId]/page.tsx`

```
<<<<<<< SEARCH
        case 1: // Personal Information
          return (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Legal Name
                </label>
                <input
                  type="text"
                  value={formData.full_name || ''}
                  onChange={(e) => updateField('full_name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter your full legal name"
                />
              </div>
=======
        case 1: // Personal Information
          return (
            <div className="space-y-4">
              <div className="grid grid-cols-5 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    First Name
                  </label>
                  <input
                    type="text"
                    value={formData.first_name || ''}
                    onChange={(e) => updateField('first_name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="First name"
                  />
                </div>
                <div className="col-span-1">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    M.I.
                  </label>
                  <input
                    type="text"
                    value={formData.middle_initial || ''}
                    onChange={(e) => updateField('middle_initial', e.target.value.slice(0, 1).toUpperCase())}
                    maxLength={1}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="M"
                  />
                </div>
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Last Name
                  </label>
                  <input
                    type="text"
                    value={formData.last_name || ''}
                    onChange={(e) => updateField('last_name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Last name"
                  />
                </div>
              </div>
>>>>>>> REPLACE
```

## Step 2: Backend — Update DD-214 field mapping

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`

```
<<<<<<< SEARCH
                field_map = {
                    'service_member_name': 'full_name',
                    'branch': 'branch',
                    'entry_date': 'service_start_date',
                    'separation_date': 'service_end_date',
                    'discharge_type': 'discharge_type',
                    'grade_rank': 'rank',
                }
=======
                field_map = {
                    'service_member_first': 'first_name',
                    'service_member_middle_initial': 'middle_initial',
                    'service_member_last': 'last_name',
                    'branch': 'branch',
                    'entry_date': 'service_start_date',
                    'separation_date': 'service_end_date',
                    'discharge_type': 'discharge_type',
                    'grade_rank': 'rank',
                }
>>>>>>> REPLACE
```

## Step 3: Backend — Update DD-214 OCR extraction prompt

File: `/ganuda/vetassist/backend/app/services/ocr_service.py`

```
<<<<<<< SEARCH
            "dd214": """Extract the following from this DD-214 document:
- full_name: Veteran's full name
- ssn_last4: Last 4 of SSN (if visible)
- branch: Branch of service
=======
            "dd214": """Extract the following from this DD-214 document:
- service_member_first: Veteran's first name
- service_member_middle_initial: Veteran's middle initial (single letter)
- service_member_last: Veteran's last name
- ssn_last4: Last 4 of SSN (if visible)
- branch: Branch of service
>>>>>>> REPLACE
```

## Step 4: Backend — Update PDF form field mappings

File: `/ganuda/vetassist/backend/app/services/pdf_service.py`

```
<<<<<<< SEARCH
    "21-526EZ": {
        "full_name": "form1[0].#subform[0].VeteransLastName[0]",
        "ssn": "form1[0].#subform[0].VeteransSocialSecurityNumber[0]",
        "date_of_birth": "form1[0].#subform[0].VeteransDateOfBirth[0]",
=======
    "21-526EZ": {
        "first_name": "form1[0].#subform[0].VeteransFirstName[0]",
        "middle_initial": "form1[0].#subform[0].VeteransMiddleInitial[0]",
        "last_name": "form1[0].#subform[0].VeteransLastName[0]",
        "ssn": "form1[0].#subform[0].VeteransSocialSecurityNumber[0]",
        "date_of_birth": "form1[0].#subform[0].VeteransDateOfBirth[0]",
>>>>>>> REPLACE
```

## Verification

After all 4 steps:
1. Start a new 21-526EZ wizard session
2. Step 1 should show 3 name fields in a grid: First Name (2 cols), M.I. (1 col), Last Name (2 cols)
3. Middle initial input should auto-uppercase and limit to 1 character
4. Saved step data should have `first_name`, `middle_initial`, `last_name` as separate keys in the JSONB answers
5. Existing sessions with `full_name` will still display in ReviewStep via `flattenStepData()` — no migration needed for in-progress sessions
