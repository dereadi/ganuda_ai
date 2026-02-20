# Jr Instruction: SAG Unified Interface — Authentication + Secrets Management Tab

**Task ID:** SAG-SECRETS-001
**Priority:** P1
**Date:** February 8, 2026
**Node:** redfin (192.168.132.223) — SAG app on port 4000
**Assigned:** Software Engineer Jr.
**Council Vote:** #8476 — Approved Option (a): Custom tab with VetAssist RBAC patterns + Fernet encryption
**Depends On:** None (standalone enhancement to SAG)

## Overview

The SAG Unified Interface (Flask app, port 4000) currently has **NO authentication**. We need to:
1. Add login/session authentication to SAG
2. Add role-based access control (RBAC) with user tiers
3. Add a "Secrets Management" tab for viewing/editing federation secrets
4. Encrypt secrets at rest in PostgreSQL using Fernet
5. Audit log all secret access

### Users

| User | Role | Access Level | Status |
|------|------|-------------|--------|
| Darrell (dereadi) | Admin | Full access — all secrets, user management | Active |
| Joe | Member | Read/write — assigned secrets only | Active |
| Kenzie | Member | Read/write — assigned secrets only | Active |
| Erika | Limited | Read-only — non-sensitive secrets only | Future |
| AI Agents | Service | API key access — per-service secrets | Active |

### Architecture Decisions
- **Framework:** Flask (SAG is already Flask — do NOT introduce FastAPI for this)
- **Auth:** Flask-Login with session cookies (bcrypt password hashing)
- **RBAC:** 4-tier model adapted from VetAssist pattern
- **Encryption:** Fernet symmetric encryption (Python `cryptography` library)
- **Storage:** PostgreSQL on bluefin (zammad_production database)
- **Audit:** All access logged to `secrets_audit_log` table

## Part 1: Database Schema

### Step 1.1: Create tables on bluefin

Connect to PostgreSQL on bluefin and run:

```sql
-- User accounts for SAG console
CREATE TABLE IF NOT EXISTS sag_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(128),
    role_tier INTEGER DEFAULT 1 NOT NULL,
    -- Tier 0: DISABLED (no access)
    -- Tier 1: LIMITED (read-only, subset of secrets)
    -- Tier 2: MEMBER (read/write assigned secrets)
    -- Tier 3: ADMIN (full access, user management)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    created_by VARCHAR(64)
);

-- Secrets vault with Fernet encryption
CREATE TABLE IF NOT EXISTS secrets_vault (
    id SERIAL PRIMARY KEY,
    secret_name VARCHAR(255) UNIQUE NOT NULL,
    secret_value_encrypted TEXT NOT NULL,
    category VARCHAR(100) DEFAULT 'general',
    -- Categories: database, camera, api_key, service_account, certificate, general
    description TEXT,
    min_tier_required INTEGER DEFAULT 3,
    -- Minimum role_tier needed to view this secret
    created_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    modified_by VARCHAR(64),
    modified_at TIMESTAMP,
    rotation_due DATE,
    metadata JSONB DEFAULT '{}'
);

-- Audit log for all secret access
CREATE TABLE IF NOT EXISTS secrets_audit_log (
    id SERIAL PRIMARY KEY,
    secret_name VARCHAR(255) NOT NULL,
    action VARCHAR(50) NOT NULL,
    -- Actions: view, create, update, delete, unauthorized_attempt
    username VARCHAR(64) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),
    details TEXT
);

-- Indexes
CREATE INDEX idx_secrets_vault_category ON secrets_vault(category);
CREATE INDEX idx_secrets_vault_tier ON secrets_vault(min_tier_required);
CREATE INDEX idx_secrets_audit_user ON secrets_audit_log(username);
CREATE INDEX idx_secrets_audit_secret ON secrets_audit_log(secret_name);
CREATE INDEX idx_secrets_audit_time ON secrets_audit_log(timestamp DESC);

-- Insert initial admin user (password: changeme — MUST be changed on first login)
-- bcrypt hash of 'changeme': generate at runtime, placeholder below
-- INSERT INTO sag_users (username, email, password_hash, display_name, role_tier, created_by)
-- VALUES ('dereadi', 'darrell@cherokee.ai', '<bcrypt_hash>', 'Darrell', 3, 'system');
```

### Step 1.2: Create initial admin user

```python
# Run this one-time on redfin to create the admin user:
import bcrypt
password = b'changeme'  # User MUST change on first login
hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode()
print(f"INSERT INTO sag_users (username, email, password_hash, display_name, role_tier, created_by) VALUES ('dereadi', NULL, '{hashed}', 'Darrell', 3, 'system');")
# Run the output SQL on bluefin
```

## Part 2: Backend — Authentication

### Step 2.1: Install dependencies

```bash
# On redfin, in the SAG venv:
pip install flask-login bcrypt cryptography
```

### Step 2.2: Add auth module

**Create file:** `/ganuda/home/dereadi/sag_unified_interface/sag_auth.py`

This module provides:

```python
"""
SAG Authentication & RBAC Module
Cherokee AI Federation - For Seven Generations

Adapted from VetAssist RBAC pattern (4-tier model).
"""
import functools
import bcrypt
import psycopg2
from flask import session, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from datetime import datetime

# --- RBAC Tier Definitions ---
class Tier:
    DISABLED = 0   # No access
    LIMITED = 1    # Read-only, subset of secrets
    MEMBER = 2     # Read/write assigned secrets
    ADMIN = 3      # Full access, user management

TIER_NAMES = {
    0: 'Disabled',
    1: 'Limited',
    2: 'Member',
    3: 'Admin'
}

# --- User Model ---
class SAGUser(UserMixin):
    def __init__(self, id, username, email, display_name, role_tier, is_active):
        self.id = id
        self.username = username
        self.email = email
        self.display_name = display_name
        self.role_tier = role_tier
        self._is_active = is_active

    @property
    def is_active(self):
        return self._is_active and self.role_tier > Tier.DISABLED

    def has_tier(self, minimum_tier):
        return self.role_tier >= minimum_tier

# --- Decorator for tier-based access ---
def require_tier(minimum_tier):
    """Flask decorator: require minimum RBAC tier."""
    def decorator(f):
        @functools.wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.has_tier(minimum_tier):
                # Log unauthorized attempt
                log_secret_access(
                    secret_name='N/A',
                    action='unauthorized_attempt',
                    username=current_user.username,
                    details=f'Attempted {request.endpoint}, needed tier {minimum_tier}, has tier {current_user.role_tier}'
                )
                if request.is_json:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- Database helpers ---
def get_db():
    """Get PostgreSQL connection using secrets_loader pattern."""
    import sys
    sys.path.insert(0, '/ganuda')
    from lib.secrets_loader import get_db_config
    cfg = get_db_config('CHEROKEE')
    return psycopg2.connect(
        host=cfg['host'], port=cfg['port'],
        dbname=cfg['dbname'], user=cfg['user'],
        password=cfg['password']
    )

def load_user_by_id(user_id):
    """Flask-Login user_loader callback."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, email, display_name, role_tier, is_active FROM sag_users WHERE id = %s",
        (user_id,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return SAGUser(*row)
    return None

def authenticate_user(username, password):
    """Verify username + password, return SAGUser or None."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, email, display_name, role_tier, is_active, password_hash FROM sag_users WHERE username = %s",
        (username,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row and bcrypt.checkpw(password.encode(), row[6].encode()):
        return SAGUser(row[0], row[1], row[2], row[3], row[4], row[5])
    return None

def log_secret_access(secret_name, action, username, details=None):
    """Write to secrets_audit_log."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO secrets_audit_log (secret_name, action, username, ip_address, user_agent, details)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (secret_name, action, username,
             request.remote_addr if request else None,
             request.user_agent.string if request else None,
             details)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass  # Audit logging should never break the app

# --- Login Manager Setup ---
def init_auth(app):
    """Initialize Flask-Login on the SAG app."""
    app.secret_key = app.config.get('SECRET_KEY', 'changeme-generate-a-real-key')
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def _load_user(user_id):
        return load_user_by_id(user_id)

    return login_manager
```

### Step 2.3: Add login/logout routes to app.py

Add to the SAG app.py:

```python
from sag_auth import init_auth, authenticate_user, require_tier, Tier, log_secret_access
from flask_login import login_user, logout_user, login_required, current_user

# Initialize auth (call after app = Flask(__name__))
init_auth(app)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = authenticate_user(username, password)
        if user and user.is_active:
            login_user(user, remember=True)
            # Update last_login
            conn = get_db()
            cur = conn.cursor()
            cur.execute("UPDATE sag_users SET last_login = NOW() WHERE id = %s", (user.id,))
            conn.commit()
            cur.close()
            conn.close()
            next_page = request.args.get('next', url_for('dashboard'))
            return redirect(next_page)
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
```

### Step 2.4: Protect existing routes

Add `@login_required` to all existing SAG routes. The dashboard and all API endpoints should require login. Example:

```python
@app.route('/')
@login_required
def dashboard():
    ...
```

## Part 3: Backend — Secrets Management

### Step 3.1: Add secrets module

**Create file:** `/ganuda/home/dereadi/sag_unified_interface/sag_secrets.py`

This module provides:

```python
"""
SAG Secrets Manager — Fernet-encrypted secrets in PostgreSQL
Cherokee AI Federation - For Seven Generations
"""
import os
from cryptography.fernet import Fernet
from sag_auth import get_db, log_secret_access, require_tier, Tier
from flask import Blueprint, request, jsonify, render_template
from flask_login import current_user, login_required

secrets_bp = Blueprint('secrets', __name__, url_prefix='/secrets')

# --- Encryption Key Management ---
ENCRYPTION_KEY_PATH = '/ganuda/config/secrets_encryption.key'

def get_fernet():
    """Load or create Fernet encryption key."""
    if not os.path.exists(ENCRYPTION_KEY_PATH):
        key = Fernet.generate_key()
        with open(ENCRYPTION_KEY_PATH, 'wb') as f:
            f.write(key)
        os.chmod(ENCRYPTION_KEY_PATH, 0o600)
    with open(ENCRYPTION_KEY_PATH, 'rb') as f:
        key = f.read()
    return Fernet(key)

fernet = get_fernet()

# --- Routes ---

@secrets_bp.route('/')
@login_required
def secrets_page():
    """Render secrets management page."""
    return render_template('secrets.html')

@secrets_bp.route('/api/list')
@login_required
def list_secrets():
    """List secrets visible to current user's tier."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """SELECT id, secret_name, category, description, min_tier_required,
                  created_by, created_at, modified_by, modified_at, rotation_due
           FROM secrets_vault
           WHERE min_tier_required <= %s
           ORDER BY category, secret_name""",
        (current_user.role_tier,)
    )
    columns = [d[0] for d in cur.description]
    secrets = [dict(zip(columns, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    # Convert timestamps to ISO strings
    for s in secrets:
        for k in ('created_at', 'modified_at', 'rotation_due'):
            if s.get(k):
                s[k] = s[k].isoformat()
    return jsonify({'secrets': secrets, 'user_tier': current_user.role_tier})

@secrets_bp.route('/api/get/<secret_name>')
@login_required
def get_secret(secret_name):
    """Retrieve and decrypt a secret (audit logged)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT secret_value_encrypted, min_tier_required FROM secrets_vault WHERE secret_name = %s",
        (secret_name,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({'error': 'Secret not found'}), 404

    encrypted_value, min_tier = row
    if current_user.role_tier < min_tier:
        log_secret_access(secret_name, 'unauthorized_attempt', current_user.username,
                         f'Tier {current_user.role_tier} < required {min_tier}')
        return jsonify({'error': 'Insufficient permissions'}), 403

    decrypted = fernet.decrypt(encrypted_value.encode()).decode()
    log_secret_access(secret_name, 'view', current_user.username)
    return jsonify({'secret_name': secret_name, 'value': decrypted})

@secrets_bp.route('/api/create', methods=['POST'])
@require_tier(Tier.ADMIN)
def create_secret():
    """Create a new secret (admin only)."""
    data = request.json
    name = data.get('secret_name', '').strip()
    value = data.get('secret_value', '')
    category = data.get('category', 'general')
    description = data.get('description', '')
    min_tier = data.get('min_tier_required', Tier.ADMIN)

    if not name or not value:
        return jsonify({'error': 'secret_name and secret_value are required'}), 400

    encrypted = fernet.encrypt(value.encode()).decode()

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO secrets_vault (secret_name, secret_value_encrypted, category, description, min_tier_required, created_by)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (name, encrypted, category, description, min_tier, current_user.username)
        )
        conn.commit()
        log_secret_access(name, 'create', current_user.username)
        return jsonify({'status': 'created', 'secret_name': name})
    except Exception as e:
        conn.rollback()
        if 'unique' in str(e).lower():
            return jsonify({'error': f'Secret "{name}" already exists. Use update instead.'}), 409
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@secrets_bp.route('/api/update', methods=['PUT'])
@require_tier(Tier.ADMIN)
def update_secret():
    """Update an existing secret (admin only)."""
    data = request.json
    name = data.get('secret_name', '').strip()
    value = data.get('secret_value', '')

    if not name or not value:
        return jsonify({'error': 'secret_name and secret_value are required'}), 400

    encrypted = fernet.encrypt(value.encode()).decode()

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """UPDATE secrets_vault SET secret_value_encrypted = %s, modified_by = %s, modified_at = NOW()
           WHERE secret_name = %s""",
        (encrypted, current_user.username, name)
    )
    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({'error': 'Secret not found'}), 404
    conn.commit()
    cur.close()
    conn.close()
    log_secret_access(name, 'update', current_user.username)
    return jsonify({'status': 'updated', 'secret_name': name})

@secrets_bp.route('/api/delete/<secret_name>', methods=['DELETE'])
@require_tier(Tier.ADMIN)
def delete_secret(secret_name):
    """Delete a secret (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM secrets_vault WHERE secret_name = %s", (secret_name,))
    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({'error': 'Secret not found'}), 404
    conn.commit()
    cur.close()
    conn.close()
    log_secret_access(secret_name, 'delete', current_user.username)
    return jsonify({'status': 'deleted', 'secret_name': secret_name})

@secrets_bp.route('/api/audit')
@require_tier(Tier.ADMIN)
def audit_log():
    """View audit log (admin only)."""
    limit = request.args.get('limit', 100, type=int)
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """SELECT id, secret_name, action, username, ip_address, timestamp, details
           FROM secrets_audit_log ORDER BY timestamp DESC LIMIT %s""",
        (limit,)
    )
    columns = [d[0] for d in cur.description]
    logs = [dict(zip(columns, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    for l in logs:
        if l.get('timestamp'):
            l['timestamp'] = l['timestamp'].isoformat()
    return jsonify({'audit_log': logs})
```

### Step 3.2: Register blueprint in app.py

Add to app.py:

```python
from sag_secrets import secrets_bp
app.register_blueprint(secrets_bp)
```

## Part 4: Frontend Templates

### Step 4.1: Login page

**Create file:** `/ganuda/home/dereadi/sag_unified_interface/templates/login.html`

Create a simple, clean login page matching SAG's existing dark theme:
- Username and password fields
- Submit button
- Flash message area for errors
- Cherokee AI Federation branding
- No registration link (admin creates accounts)

### Step 4.2: Secrets management page

**Create file:** `/ganuda/home/dereadi/sag_unified_interface/templates/secrets.html`

The secrets page should include:

**For all authenticated users:**
- Table listing secrets they can see (name, category, description, last modified)
- "Reveal" button per secret (click to decrypt and show, audit logged)
- Copy-to-clipboard button
- Search/filter by category
- Value is hidden by default (shown as ••••••••)

**For ADMIN tier only:**
- "Add Secret" button → modal form (name, value, category, description, min_tier)
- "Edit" button per secret → update value
- "Delete" button with confirmation dialog
- "Audit Log" tab showing who accessed what and when
- "User Management" tab (create/edit users, set tiers)

**Categories for dropdown:**
- database, camera, api_key, service_account, certificate, telegram, general

### Step 4.3: User management page (admin only)

**Create file:** `/ganuda/home/dereadi/sag_unified_interface/templates/users.html`

Admin-only page showing:
- Table of all users (username, display name, tier, last login, active)
- "Add User" button
- "Edit Tier" and "Deactivate" buttons per user
- Password reset functionality

### Step 4.4: Add secrets tab to SAG navigation

Update the SAG navigation bar to include:
- "Secrets" tab (visible to all logged-in users)
- "Users" tab (visible to ADMIN tier only)
- Current user display + "Logout" link

## Part 5: Seed Initial Secrets

### Step 5.1: Import existing secrets from secrets.env

After deploying, run a one-time import script:

```python
"""
One-time import: secrets.env → secrets_vault (encrypted)
Run on redfin after Part 1-3 are deployed.
"""
import os
from cryptography.fernet import Fernet

# Load encryption key
with open('/ganuda/config/secrets_encryption.key', 'rb') as f:
    fernet = Fernet(f.read())

# Parse secrets.env
secrets = {}
with open('/ganuda/config/secrets.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            secrets[key.strip()] = value.strip()

# Map to categories
CATEGORY_MAP = {
    'CHEROKEE_DB': 'database',
    'TELEGRAM': 'telegram',
    'LLM_GATEWAY': 'api_key',
    'CAMERA': 'camera',
}

def categorize(key):
    for prefix, cat in CATEGORY_MAP.items():
        if key.startswith(prefix):
            return cat
    return 'general'

# Insert into secrets_vault
import psycopg2
conn = psycopg2.connect(host='192.168.132.222', port=5432, dbname='zammad_production',
                         user='claude', password=os.environ['CHEROKEE_DB_PASS'])
cur = conn.cursor()
for key, value in secrets.items():
    encrypted = fernet.encrypt(value.encode()).decode()
    tier = 3  # Default: admin only
    if key.startswith('LLM_GATEWAY_URL'):
        tier = 2  # Members can see gateway URL
    cur.execute(
        """INSERT INTO secrets_vault (secret_name, secret_value_encrypted, category, description, min_tier_required, created_by)
           VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (secret_name) DO NOTHING""",
        (key, encrypted, categorize(key), f'Imported from secrets.env', tier, 'system')
    )
conn.commit()
cur.close()
conn.close()
print(f"Imported {len(secrets)} secrets")
```

## Part 6: Deployment

### Step 6.1: Deploy on redfin

```bash
# Install deps
cd /ganuda/home/dereadi/sag_unified_interface
pip install flask-login bcrypt cryptography

# Generate encryption key
python3 -c "
from cryptography.fernet import Fernet
import os
key = Fernet.generate_key()
path = '/ganuda/config/secrets_encryption.key'
with open(path, 'wb') as f: f.write(key)
os.chmod(path, 0o600)
print(f'Key written to {path}')
"

# Create initial admin user
python3 -c "
import bcrypt
h = bcrypt.hashpw(b'changeme', bcrypt.gensalt()).decode()
print(f\"INSERT INTO sag_users (username, display_name, password_hash, role_tier, created_by) VALUES ('dereadi', 'Darrell', '{h}', 3, 'system');\")
" | ssh dereadi@192.168.132.222 "PGPASSWORD=\$CHEROKEE_DB_PASS psql -h 192.168.132.222 -U claude -d zammad_production"

# Run schema migration on bluefin
# (copy the SQL from Part 1 Step 1.1)

# Restart SAG
sudo systemctl restart sag-unified
```

### Step 6.2: Verify

```bash
# Test login page renders
curl -s http://localhost:4000/login | grep -i "login"

# Test redirect when not authenticated
curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/

# Test API
curl -s -c cookies.txt -X POST http://localhost:4000/login \
    -d "username=dereadi&password=changeme"
curl -s -b cookies.txt http://localhost:4000/secrets/api/list | python3 -m json.tool
```

## Security Checklist

- [ ] Encryption key file has 0600 permissions
- [ ] No secrets in plaintext in Python source files
- [ ] bcrypt used for password hashing (NOT md5/sha)
- [ ] All routes decorated with `@login_required`
- [ ] Admin routes use `@require_tier(Tier.ADMIN)`
- [ ] Audit log captures all secret reads, writes, and unauthorized attempts
- [ ] Session cookie has `httponly=True` and `secure=True` (when behind HTTPS)
- [ ] Crawdad security review before production deployment
- [ ] Encryption key backed up securely (NOT in git)

## Rollback

If the secrets tab breaks SAG:
```bash
# Remove the blueprint import from app.py
# Remove @login_required decorators
# Restart SAG
sudo systemctl restart sag-unified
```

The database tables persist safely — no data loss on rollback.

## Future: Phase 2 Evaluation

When we outgrow the custom tab (>10 users, need dynamic secrets, approval workflows):
- Evaluate **Infisical** (24.8k GitHub stars, PostgreSQL-native, LDAP auth)
- Migrate `secrets_vault` data to Infisical
- Keep `secrets_loader.py` as abstraction layer, point tier-1 at Infisical API
- Council vote required before migration

---
**FOR SEVEN GENERATIONS** — Protect secrets today so they remain secret for generations.
