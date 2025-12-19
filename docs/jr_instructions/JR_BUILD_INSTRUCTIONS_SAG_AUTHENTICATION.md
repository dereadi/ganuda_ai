# Jr Build Instructions: SAG Authentication System
## Priority: HIGH - Security Boundary for Private ITSM

---

## Objective

Implement authentication for SAG Unified Interface to ensure only authorized users can access the control plane. This protects settings, alerts, IoT controls, and sensitive operational data.

**Principle**: Public sees stats, private controls the system.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     INTERNET / NETWORK                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
            ▼                               ▼
┌─────────────────────┐         ┌─────────────────────────────────┐
│   ganuda.us         │         │   SAG (192.168.132.223:4000)    │
│   PUBLIC            │         │   PRIVATE                        │
│   No Auth           │         │                                  │
│   Read-only stats   │         │   ┌─────────────────────────┐   │
└─────────────────────┘         │   │     LOGIN SCREEN        │   │
                                │   │  Username / Password     │   │
                                │   └───────────┬─────────────┘   │
                                │               │                  │
                                │               ▼                  │
                                │   ┌─────────────────────────┐   │
                                │   │   SESSION VALIDATION    │   │
                                │   │   - Check cookie/token  │   │
                                │   │   - Verify permissions  │   │
                                │   └───────────┬─────────────┘   │
                                │               │                  │
                                │               ▼                  │
                                │   ┌─────────────────────────┐   │
                                │   │   CONTROL ROOM          │   │
                                │   │   Full access           │   │
                                │   └─────────────────────────┘   │
                                └─────────────────────────────────┘
```

---

## Authentication Options

### Option A: Simple Username/Password (Recommended for Start)

Single admin account, session-based authentication.

**Pros**: Simple, quick to implement, sufficient for small team
**Cons**: No role-based access, single account

### Option B: Multi-User with Roles

Multiple user accounts with different permission levels.

**Pros**: Granular access control, audit per user
**Cons**: More complex, requires user management UI

### Option C: SSO Integration (Future)

LDAP, OAuth, or SAML integration.

**Pros**: Enterprise-ready, centralized auth
**Cons**: Complex setup, external dependencies

---

## Implementation: Option A (Simple Auth)

### Task 1: Add User Table

```sql
-- Run on bluefin (zammad_production)
CREATE TABLE IF NOT EXISTS sag_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'operator',  -- admin, operator, viewer
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create index for fast lookups
CREATE INDEX idx_sag_users_username ON sag_users(username);

-- Insert default admin user (CHANGE PASSWORD IMMEDIATELY)
-- Password: 'changeme' - hash generated with werkzeug.security
INSERT INTO sag_users (username, password_hash, display_name, role)
VALUES (
    'admin',
    'pbkdf2:sha256:600000$SALT$HASH',  -- Generate proper hash
    'Administrator',
    'admin'
);
```

### Task 2: Add Session Table

```sql
CREATE TABLE IF NOT EXISTS sag_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES sag_users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT
);

CREATE INDEX idx_sag_sessions_session_id ON sag_sessions(session_id);
CREATE INDEX idx_sag_sessions_expires ON sag_sessions(expires_at);
```

### Task 3: Authentication Module

Create `/home/dereadi/sag_unified_interface/auth.py`:

```python
"""SAG Authentication Module"""
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import request, redirect, url_for, session, g
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2

# Configuration
SESSION_LIFETIME_HOURS = 24
DB_CONFIG = {
    "host": "192.168.132.222",
    "database": "zammad_production",
    "user": "claude",
    "password": "jawaseatlasers2"
}


def get_db():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG)


def create_user(username, password, display_name=None, role='operator'):
    """Create a new user"""
    password_hash = generate_password_hash(password)

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO sag_users (username, password_hash, display_name, role)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (username, password_hash, display_name or username, role))
        user_id = cur.fetchone()[0]
        conn.commit()
        return user_id
    except psycopg2.IntegrityError:
        conn.rollback()
        return None
    finally:
        cur.close()
        conn.close()


def verify_user(username, password):
    """Verify username and password, return user dict or None"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, username, password_hash, display_name, role, is_active
            FROM sag_users
            WHERE username = %s
        """, (username,))
        row = cur.fetchone()

        if row and row[5] and check_password_hash(row[2], password):
            # Update last login
            cur.execute("""
                UPDATE sag_users SET last_login = NOW() WHERE id = %s
            """, (row[0],))
            conn.commit()

            return {
                "id": row[0],
                "username": row[1],
                "display_name": row[3],
                "role": row[4]
            }
        return None
    finally:
        cur.close()
        conn.close()


def create_session(user_id):
    """Create a new session for user"""
    session_id = secrets.token_hex(32)
    expires_at = datetime.utcnow() + timedelta(hours=SESSION_LIFETIME_HOURS)

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO sag_sessions (session_id, user_id, expires_at, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            session_id,
            user_id,
            expires_at,
            request.remote_addr,
            request.user_agent.string[:500] if request.user_agent else None
        ))
        conn.commit()
        return session_id
    finally:
        cur.close()
        conn.close()


def validate_session(session_id):
    """Validate session and return user info or None"""
    if not session_id:
        return None

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT u.id, u.username, u.display_name, u.role
            FROM sag_sessions s
            JOIN sag_users u ON s.user_id = u.id
            WHERE s.session_id = %s
              AND s.expires_at > NOW()
              AND u.is_active = true
        """, (session_id,))
        row = cur.fetchone()

        if row:
            return {
                "id": row[0],
                "username": row[1],
                "display_name": row[2],
                "role": row[3]
            }
        return None
    finally:
        cur.close()
        conn.close()


def destroy_session(session_id):
    """Delete a session (logout)"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM sag_sessions WHERE session_id = %s", (session_id,))
        conn.commit()
    finally:
        cur.close()
        conn.close()


def cleanup_expired_sessions():
    """Remove expired sessions (call periodically)"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM sag_sessions WHERE expires_at < NOW()")
        conn.commit()
    finally:
        cur.close()
        conn.close()


def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = session.get('session_id')
        user = validate_session(session_id)

        if not user:
            # For API requests, return 401
            if request.path.startswith('/api/'):
                return {"error": "Authentication required"}, 401
            # For page requests, redirect to login
            return redirect(url_for('login', next=request.url))

        g.user = user
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if g.user.get('role') != 'admin':
            if request.path.startswith('/api/'):
                return {"error": "Admin access required"}, 403
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function
```

### Task 4: Add Login Routes to app.py

```python
# Add to app.py

from flask import session, g, redirect, url_for, flash
from auth import (
    verify_user, create_session, validate_session,
    destroy_session, login_required, admin_required
)

# Configure session
app.secret_key = os.environ.get('SAG_SECRET_KEY', secrets.token_hex(32))

# Check auth on every request
@app.before_request
def check_auth():
    # Public routes that don't require auth
    public_routes = ['/login', '/static/', '/health']

    if any(request.path.startswith(route) for route in public_routes):
        return None

    session_id = session.get('session_id')
    user = validate_session(session_id)

    if not user:
        if request.path.startswith('/api/'):
            return jsonify({"error": "Authentication required"}), 401
        return redirect(url_for('login'))

    g.user = user


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = verify_user(username, password)

        if user:
            session_id = create_session(user['id'])
            session['session_id'] = session_id

            # Log successful login
            log_audit_event('login', user['username'], 'Login successful')

            next_url = request.args.get('next', url_for('home'))
            return redirect(next_url)
        else:
            # Log failed attempt
            log_audit_event('login_failed', username, 'Invalid credentials')
            flash('Invalid username or password', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session_id = session.get('session_id')
    if session_id:
        destroy_session(session_id)
        session.pop('session_id', None)
    return redirect(url_for('login'))


def log_audit_event(event_type, username, details):
    """Log authentication events to thermal memory"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO thermal_memory_archive (memory_hash, original_content, current_stage)
            VALUES (%s, %s, 'FRESH')
        """, (
            hashlib.sha256(f"{event_type}:{username}:{datetime.utcnow()}".encode()).hexdigest(),
            json.dumps({
                "type": "auth_event",
                "event": event_type,
                "username": username,
                "details": details,
                "ip": request.remote_addr,
                "timestamp": datetime.utcnow().isoformat()
            })
        ))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Failed to log auth event: {e}")
```

### Task 5: Create Login Template

Create `/home/dereadi/sag_unified_interface/templates/login.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SAG Login | Cherokee AI Federation</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #e6edf3;
        }

        .login-container {
            background: #21262d;
            border-radius: 12px;
            padding: 40px;
            width: 100%;
            max-width: 400px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }

        .login-header {
            text-align: center;
            margin-bottom: 30px;
        }

        .login-header h1 {
            font-size: 1.5rem;
            margin-bottom: 8px;
        }

        .login-header .subtitle {
            color: #8b949e;
            font-size: 0.9rem;
        }

        .logo {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #2dd4bf, #14b8a6);
            border-radius: 12px;
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-size: 0.9rem;
            color: #8b949e;
        }

        .form-group input {
            width: 100%;
            padding: 12px 16px;
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            color: #e6edf3;
            font-size: 1rem;
            transition: border-color 0.2s;
        }

        .form-group input:focus {
            outline: none;
            border-color: #2dd4bf;
        }

        .login-button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #2dd4bf, #14b8a6);
            border: none;
            border-radius: 6px;
            color: #0d1117;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .login-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(45, 212, 191, 0.3);
        }

        .error-message {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid #ef4444;
            color: #ef4444;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 0.9rem;
        }

        .footer {
            text-align: center;
            margin-top: 30px;
            color: #8b949e;
            font-size: 0.8rem;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <div class="logo">SAG</div>
            <h1>Cherokee AI Federation</h1>
            <p class="subtitle">SAG Unified Interface</p>
        </div>

        {% if get_flashed_messages() %}
        <div class="error-message">
            {% for message in get_flashed_messages() %}
            {{ message }}
            {% endfor %}
        </div>
        {% endif %}

        <form method="POST" action="{{ url_for('login') }}">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required autofocus>
            </div>

            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>

            <button type="submit" class="login-button">Sign In</button>
        </form>

        <div class="footer">
            <p>For Seven Generations</p>
        </div>
    </div>
</body>
</html>
```

### Task 6: Add User Display to UI

Update `index.html` to show logged-in user:

```html
<!-- In the header/command bar area -->
<div class="user-info">
    <span class="user-name">{{ g.user.display_name }}</span>
    <a href="{{ url_for('logout') }}" class="logout-btn">Logout</a>
</div>
```

Add CSS:

```css
.user-info {
    display: flex;
    align-items: center;
    gap: 12px;
}

.user-name {
    color: var(--text-secondary);
    font-size: 0.9rem;
}

.logout-btn {
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 0.85rem;
    padding: 4px 12px;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    transition: all 0.2s;
}

.logout-btn:hover {
    color: var(--text-primary);
    border-color: var(--accent-color);
}
```

---

## Role-Based Access (Future Enhancement)

### Permission Levels

| Role | Can View | Can Edit | Can Admin |
|------|----------|----------|-----------|
| viewer | Dashboard, Stats | Nothing | Nothing |
| operator | Everything | Settings, Alerts | Nothing |
| admin | Everything | Everything | Users, System |

### Implementation

```python
# Permission decorator
def permission_required(permission):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            role = g.user.get('role', 'viewer')

            permissions = {
                'viewer': ['view'],
                'operator': ['view', 'edit'],
                'admin': ['view', 'edit', 'admin']
            }

            if permission not in permissions.get(role, []):
                if request.path.startswith('/api/'):
                    return {"error": "Permission denied"}, 403
                flash('You do not have permission to access this feature', 'error')
                return redirect(url_for('home'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Usage
@app.route('/api/settings', methods=['POST'])
@permission_required('edit')
def update_settings():
    # Only operators and admins can edit
    pass

@app.route('/api/users', methods=['POST'])
@permission_required('admin')
def manage_users():
    # Only admins
    pass
```

---

## Network Security Options

### Option 1: Login Screen Only
- SAG accessible on LAN
- Login required for all access
- Simplest setup

### Option 2: VPN/Tailscale + Login
- SAG only accessible via VPN
- Login as second factor
- More secure

### Option 3: IP Allowlist + Login
- Restrict to known IPs
- Login still required
- Good for static networks

```python
# IP allowlist middleware
ALLOWED_IPS = ['192.168.132.0/24', '10.0.0.0/8']

@app.before_request
def check_ip():
    from ipaddress import ip_address, ip_network

    client_ip = ip_address(request.remote_addr)

    for allowed in ALLOWED_IPS:
        if client_ip in ip_network(allowed):
            return None

    return "Access denied", 403
```

---

## Security Checklist

- [ ] Password hashing uses strong algorithm (pbkdf2/bcrypt)
- [ ] Session tokens are cryptographically random
- [ ] Sessions expire after inactivity
- [ ] Failed login attempts are rate-limited
- [ ] All auth events logged to audit trail
- [ ] HTTPS enforced (when deployed publicly)
- [ ] Session cookies have Secure and HttpOnly flags
- [ ] CSRF protection enabled
- [ ] Password complexity requirements enforced

---

## Initial Setup Commands

```bash
# On bluefin - create tables
PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production << 'EOF'
CREATE TABLE IF NOT EXISTS sag_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'operator',
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sag_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES sag_users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT
);

CREATE INDEX IF NOT EXISTS idx_sag_users_username ON sag_users(username);
CREATE INDEX IF NOT EXISTS idx_sag_sessions_session_id ON sag_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sag_sessions_expires ON sag_sessions(expires_at);
EOF

# Create initial admin user (run in Python)
python3 << 'EOF'
from werkzeug.security import generate_password_hash
import psycopg2

password = 'CHANGE_THIS_PASSWORD'
hash = generate_password_hash(password)

conn = psycopg2.connect(
    host='192.168.132.222',
    database='zammad_production',
    user='claude',
    password='jawaseatlasers2'
)
cur = conn.cursor()
cur.execute("""
    INSERT INTO sag_users (username, password_hash, display_name, role)
    VALUES ('admin', %s, 'Administrator', 'admin')
    ON CONFLICT (username) DO UPDATE SET password_hash = %s
""", (hash, hash))
conn.commit()
print("Admin user created/updated")
EOF
```

---

## Testing Checklist

- [ ] Login page renders correctly
- [ ] Valid credentials grant access
- [ ] Invalid credentials show error
- [ ] Session persists across page loads
- [ ] Logout destroys session
- [ ] Expired sessions redirect to login
- [ ] API requests without auth return 401
- [ ] Login events logged to audit
- [ ] Password change works
- [ ] Multiple concurrent sessions work

---

## Success Criteria

1. ✅ SAG requires login before showing any control functions
2. ✅ Sessions expire after configured time
3. ✅ All auth events logged
4. ✅ Logout fully destroys session
5. ✅ Clean, professional login UI
6. ✅ API endpoints protected

---

*For Seven Generations*
