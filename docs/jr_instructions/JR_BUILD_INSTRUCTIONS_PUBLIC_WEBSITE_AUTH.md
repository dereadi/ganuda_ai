# Jr Build Instructions: Public Website with Authentication
## Priority: HIGH - Required Before Public Launch
## Status: PLANNED (Post Phase 4)

---

## Objective

Separate ganuda.us into:
1. **Public Landing Page** - No auth required, marketing/info content
2. **Dashboard/Control Room** - Auth required, operational interface

---

## Architecture

```
https://ganuda.us/
├── / (public)              → Landing page, features, docs
├── /about (public)         → About Cherokee AI Federation
├── /docs (public)          → Public documentation
├── /status (public)        → Public status page (limited info)
│
├── /login                  → Authentication page
├── /dashboard (protected)  → SAG Control Room
├── /api/* (protected)      → All API endpoints
└── /admin (protected)      → Admin functions
```

---

## Public Pages Content

### Landing Page (/)
- Hero: "Cherokee AI Federation - Private AI Infrastructure"
- Features overview (Council, Memory, Security)
- "For Seven Generations" philosophy
- CTA: "Login to Dashboard" / "Request Access"

### Status Page (/status)
- Federation health (green/yellow/red)
- Uptime percentage
- Last incident (if any)
- NO sensitive details

### Docs (/docs)
- Public API documentation
- Getting started guide
- Architecture overview

---

## Authentication Options

### Option 1: Simple Session Auth (MVP)
```python
from flask_login import LoginManager, login_required

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')
```

### Option 2: OAuth (Google/GitHub)
- Better for team access
- No password management

### Option 3: Tailscale Auth (Recommended for Internal)
- If on Tailscale network → auto-authenticated
- Public users → see public pages only

---

## Implementation Tasks

### Task 1: Split Templates
- `templates/public/` - Landing, about, docs, status
- `templates/dashboard/` - Current control room (protected)

### Task 2: Add Authentication
- Flask-Login or Flask-Security
- Session management
- API key auth for /api/*

### Task 3: Create Landing Page
- Clean, professional design
- Cherokee branding
- Mobile responsive

### Task 4: Route Protection
```python
# Public routes
@app.route('/')
def landing():
    return render_template('public/landing.html')

# Protected routes
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard/index.html')
```

### Task 5: API Authentication
- Existing API key system for programmatic access
- Session auth for browser access

---

## Security Considerations

- [ ] CSRF protection on all forms
- [ ] Rate limiting on login attempts
- [ ] Secure session cookies (HttpOnly, Secure, SameSite)
- [ ] Password hashing (if using password auth)
- [ ] Audit logging for auth events

---

## Success Criteria

1. ✅ Public can view landing/docs without login
2. ✅ Dashboard requires authentication
3. ✅ API endpoints require API key or session
4. ✅ No sensitive data exposed on public pages
5. ✅ Clean separation of public/private content

---

*For Seven Generations*
