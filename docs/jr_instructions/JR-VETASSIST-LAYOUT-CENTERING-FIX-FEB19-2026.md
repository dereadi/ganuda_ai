# Jr Instruction: Fix VetAssist Layout — Fields Bunched to Left

**Task ID**: VETASSIST-LAYOUT-001
**Priority**: 1 (critical — reported by Dr. Joe in live demo)
**Assigned Jr**: Software Engineer Jr.
**Story Points**: 2
**use_rlm**: false

## Context

Dr. Joe reports VetAssist fields are "all bunched to the left" and not rendering correctly. Root cause: the Tailwind container config only defines a `2xl: 1400px` breakpoint — no max-width is applied at sm, md, lg, or xl. On most screens, the container is 100% width, making form fields stretch edge-to-edge with the grid falling to single-column on anything below 1024px.

## Step 1: Add Container Breakpoints to Tailwind Config

File: `/ganuda/vetassist/frontend/tailwind.config.ts`

<<<<<<< SEARCH
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
=======
    container: {
      center: true,
      padding: "2rem",
      screens: {
        sm: "640px",
        md: "768px",
        lg: "1024px",
        xl: "1280px",
        "2xl": "1400px",
      },
    },
>>>>>>> REPLACE

## Step 2: Add Width Constraint to Main Content Area

File: `/ganuda/vetassist/frontend/app/layout.tsx`

<<<<<<< SEARCH
            <main id="main-content" className="flex-1">
=======
            <main id="main-content" className="flex-1 w-full">
>>>>>>> REPLACE

## Step 3: Constrain Calculator Form Width

File: `/ganuda/vetassist/frontend/app/calculator/page.tsx`

<<<<<<< SEARCH
        <div className="grid lg:grid-cols-2 gap-8">
=======
        <div className="grid lg:grid-cols-2 gap-8 max-w-5xl mx-auto">
>>>>>>> REPLACE

## Manual Steps (TPM)

After Jr execution on bluefin:
1. `cd /ganuda/vetassist/frontend && npm run build` (or whatever the build command is)
2. Restart the frontend service
3. Have Dr. Joe verify the layout is fixed
