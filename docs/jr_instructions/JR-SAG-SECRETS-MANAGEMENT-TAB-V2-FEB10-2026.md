# Jr Instruction: SAG Secrets Management Tab

**Task ID:** SAG-SECRETS-002
**Priority:** P1
**Assigned To:** Software Engineer Jr.
**Date:** February 10, 2026
**Kanban:** #643 (retry — previous attempt failed)

## Context

Camera passwords were rotated but there is no UI to manage secrets. The SAG Unified Interface needs a Secrets tab in the GOVERNANCE section that reads/writes `/ganuda/config/secrets.env`. Internal network only — no auth layer needed for this phase.

## Edit 1: Add secrets API routes to app.py

File: `/ganuda/home/dereadi/sag_unified_interface/app.py`

```
<<<<<<< SEARCH
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000, debug=False)
=======
# ============================================================================
# SECRETS MANAGEMENT API
# ============================================================================

SECRETS_FILE = '/ganuda/config/secrets.env'

def _parse_secrets_env():
    """Parse secrets.env into list of dicts with name, value, category."""
    secrets = []
    if not os.path.exists(SECRETS_FILE):
        return secrets
    with open(SECRETS_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                # Categorize by prefix
                if 'DB' in key or 'DATABASE' in key:
                    category = 'Database'
                elif 'CAMERA' in key:
                    category = 'Cameras'
                elif 'TELEGRAM' in key:
                    category = 'Telegram'
                elif 'LLM' in key or 'GATEWAY' in key or 'API_KEY' in key:
                    category = 'AI Services'
                else:
                    category = 'General'
                secrets.append({
                    'name': key,
                    'value': value,
                    'category': category,
                    'masked': value[:2] + '*' * max(0, len(value) - 4) + value[-2:] if len(value) > 4 else '****'
                })
    return secrets

def _write_secrets_env(secrets_dict):
    """Write updated secrets back to secrets.env preserving comments."""
    lines = []
    if os.path.exists(SECRETS_FILE):
        with open(SECRETS_FILE, 'r') as f:
            lines = f.readlines()
    new_lines = []
    updated_keys = set()
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and '=' in stripped:
            key = stripped.split('=', 1)[0].strip()
            if key in secrets_dict:
                new_lines.append(f'{key}={secrets_dict[key]}\n')
                updated_keys.add(key)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    # Add new keys
    for key, value in secrets_dict.items():
        if key not in updated_keys:
            new_lines.append(f'{key}={value}\n')
    with open(SECRETS_FILE, 'w') as f:
        f.writelines(new_lines)

@app.route('/api/secrets')
def get_secrets():
    """List all secrets with masked values."""
    try:
        secrets = _parse_secrets_env()
        return jsonify({
            'secrets': [{'name': s['name'], 'category': s['category'], 'masked': s['masked']} for s in secrets],
            'count': len(secrets),
            'file': SECRETS_FILE
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/secrets/<name>/reveal')
def reveal_secret(name):
    """Reveal a single secret value. Audit logged."""
    try:
        secrets = _parse_secrets_env()
        for s in secrets:
            if s['name'] == name:
                logger.info(f"[AUDIT] Secret revealed: {name} from {request.remote_addr}")
                return jsonify({'name': name, 'value': s['value']})
        return jsonify({'error': 'Secret not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/secrets/<name>', methods=['PUT'])
def update_secret(name):
    """Update a secret value."""
    try:
        data = request.get_json()
        new_value = data.get('value', '').strip()
        if not new_value:
            return jsonify({'error': 'Value required'}), 400
        _write_secrets_env({name: new_value})
        logger.info(f"[AUDIT] Secret updated: {name} from {request.remote_addr}")
        return jsonify({'success': True, 'name': name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/secrets', methods=['POST'])
def create_secret():
    """Create a new secret."""
    try:
        data = request.get_json()
        name = data.get('name', '').strip().upper().replace(' ', '_')
        value = data.get('value', '').strip()
        if not name or not value:
            return jsonify({'error': 'Name and value required'}), 400
        _write_secrets_env({name: value})
        logger.info(f"[AUDIT] Secret created: {name} from {request.remote_addr}")
        return jsonify({'success': True, 'name': name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000, debug=False)
>>>>>>> REPLACE
```

## Edit 2: Add Secrets nav item to GOVERNANCE section

File: `/ganuda/home/dereadi/sag_unified_interface/templates/index.html`

```
<<<<<<< SEARCH
            <div class="nav-section">
                <h4>GOVERNANCE</h4>
                <a href="#" class="nav-item" data-view="tribe">Tribe</a>
                <a href="#" class="nav-item" data-view="console">Console</a>
                <a href="#" class="nav-item" data-view="settings">Settings</a>
            </div>
=======
            <div class="nav-section">
                <h4>GOVERNANCE</h4>
                <a href="#" class="nav-item" data-view="tribe">Tribe</a>
                <a href="#" class="nav-item" data-view="console">Console</a>
                <a href="#" class="nav-item" data-view="secrets">Secrets</a>
                <a href="#" class="nav-item" data-view="settings">Settings</a>
            </div>
>>>>>>> REPLACE
```

## Edit 3: Add secrets view panel

File: `/ganuda/home/dereadi/sag_unified_interface/templates/index.html`

```
<<<<<<< SEARCH
            <div id="settings-view" class="view-content"><h2>Settings</h2><div id="settings-content"></div></div>
=======
            <div id="secrets-view" class="view-content">
                <h2>Secrets Management</h2>
                <div style="margin-bottom:16px;display:flex;gap:12px;align-items:center;">
                    <select id="secrets-category-filter" style="padding:8px 12px;background:var(--color-surface);color:var(--color-text);border:1px solid var(--color-border);border-radius:6px;">
                        <option value="all">All Categories</option>
                    </select>
                    <button onclick="showAddSecretDialog()" style="padding:8px 16px;background:var(--color-accent);color:#fff;border:none;border-radius:6px;cursor:pointer;">+ Add Secret</button>
                    <span id="secrets-count" style="color:var(--color-text-muted);margin-left:auto;"></span>
                </div>
                <table style="width:100%;border-collapse:collapse;">
                    <thead>
                        <tr style="border-bottom:2px solid var(--color-border);text-align:left;">
                            <th style="padding:10px;color:var(--color-text-muted);">Name</th>
                            <th style="padding:10px;color:var(--color-text-muted);">Category</th>
                            <th style="padding:10px;color:var(--color-text-muted);">Value</th>
                            <th style="padding:10px;color:var(--color-text-muted);">Actions</th>
                        </tr>
                    </thead>
                    <tbody id="secrets-table-body"></tbody>
                </table>
                <div id="secret-edit-dialog" style="display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);z-index:1000;display:none;align-items:center;justify-content:center;">
                    <div style="background:var(--color-surface);padding:24px;border-radius:12px;width:480px;max-width:90vw;">
                        <h3 id="secret-dialog-title" style="margin:0 0 16px 0;">Edit Secret</h3>
                        <input type="text" id="secret-dialog-name" placeholder="SECRET_NAME" style="width:100%;padding:10px;margin-bottom:12px;background:var(--color-background);color:var(--color-text);border:1px solid var(--color-border);border-radius:6px;box-sizing:border-box;">
                        <input type="text" id="secret-dialog-value" placeholder="value" style="width:100%;padding:10px;margin-bottom:16px;background:var(--color-background);color:var(--color-text);border:1px solid var(--color-border);border-radius:6px;box-sizing:border-box;">
                        <div style="display:flex;gap:12px;justify-content:flex-end;">
                            <button onclick="closeSecretDialog()" style="padding:8px 16px;background:var(--color-surface);color:var(--color-text);border:1px solid var(--color-border);border-radius:6px;cursor:pointer;">Cancel</button>
                            <button onclick="saveSecret()" style="padding:8px 16px;background:var(--color-accent);color:#fff;border:none;border-radius:6px;cursor:pointer;">Save</button>
                        </div>
                    </div>
                </div>
                <script>
                let secretsData = [];
                function loadSecrets() {
                    fetch('/api/secrets').then(r=>r.json()).then(data => {
                        secretsData = data.secrets || [];
                        document.getElementById('secrets-count').textContent = data.count + ' secrets in ' + data.file;
                        const cats = [...new Set(secretsData.map(s=>s.category))];
                        const filter = document.getElementById('secrets-category-filter');
                        filter.innerHTML = '<option value="all">All Categories</option>' + cats.map(c=>'<option value="'+c+'">'+c+'</option>').join('');
                        renderSecrets();
                    });
                }
                function renderSecrets() {
                    const filter = document.getElementById('secrets-category-filter').value;
                    const filtered = filter === 'all' ? secretsData : secretsData.filter(s=>s.category===filter);
                    const tbody = document.getElementById('secrets-table-body');
                    tbody.innerHTML = filtered.map(s => '<tr style="border-bottom:1px solid var(--color-border);">' +
                        '<td style="padding:10px;font-family:monospace;font-weight:600;">'+s.name+'</td>' +
                        '<td style="padding:10px;"><span style="padding:3px 8px;border-radius:4px;background:var(--color-surface);font-size:12px;">'+s.category+'</span></td>' +
                        '<td style="padding:10px;font-family:monospace;" id="val-'+s.name+'">'+s.masked+'</td>' +
                        '<td style="padding:10px;display:flex;gap:8px;">' +
                            '<button onclick="revealSecret(\''+s.name+'\')" style="padding:4px 10px;background:var(--color-surface);color:var(--color-text);border:1px solid var(--color-border);border-radius:4px;cursor:pointer;font-size:12px;">Reveal</button>' +
                            '<button onclick="editSecret(\''+s.name+'\')" style="padding:4px 10px;background:var(--color-surface);color:var(--color-text);border:1px solid var(--color-border);border-radius:4px;cursor:pointer;font-size:12px;">Edit</button>' +
                        '</td></tr>').join('');
                }
                function revealSecret(name) {
                    fetch('/api/secrets/'+name+'/reveal').then(r=>r.json()).then(data => {
                        const el = document.getElementById('val-'+name);
                        if (el) { el.textContent = data.value; setTimeout(()=>{ el.textContent = secretsData.find(s=>s.name===name).masked; }, 5000); }
                    });
                }
                function editSecret(name) {
                    document.getElementById('secret-dialog-title').textContent = 'Edit: ' + name;
                    document.getElementById('secret-dialog-name').value = name;
                    document.getElementById('secret-dialog-name').readOnly = true;
                    document.getElementById('secret-dialog-value').value = '';
                    document.getElementById('secret-dialog-value').placeholder = 'Enter new value';
                    document.getElementById('secret-edit-dialog').style.display = 'flex';
                }
                function showAddSecretDialog() {
                    document.getElementById('secret-dialog-title').textContent = 'Add Secret';
                    document.getElementById('secret-dialog-name').value = '';
                    document.getElementById('secret-dialog-name').readOnly = false;
                    document.getElementById('secret-dialog-value').value = '';
                    document.getElementById('secret-edit-dialog').style.display = 'flex';
                }
                function closeSecretDialog() { document.getElementById('secret-edit-dialog').style.display = 'none'; }
                function saveSecret() {
                    const name = document.getElementById('secret-dialog-name').value.trim();
                    const value = document.getElementById('secret-dialog-value').value.trim();
                    if (!name || !value) return;
                    const isNew = !document.getElementById('secret-dialog-name').readOnly;
                    const opts = { method: isNew ? 'POST' : 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify({name, value}) };
                    const url = isNew ? '/api/secrets' : '/api/secrets/' + name;
                    fetch(url, opts).then(r=>r.json()).then(data => {
                        if (data.success) { closeSecretDialog(); loadSecrets(); }
                    });
                }
                document.getElementById('secrets-category-filter').addEventListener('change', renderSecrets);
                document.querySelector('[data-view="secrets"]').addEventListener('click', loadSecrets);
                </script>
            </div>
            <div id="settings-view" class="view-content"><h2>Settings</h2><div id="settings-content"></div></div>
>>>>>>> REPLACE
```

## Do NOT

- Do not add authentication — internal network only, auth is a separate phase
- Do not modify secrets_loader.py — the API reads secrets.env directly
- Do not add encryption — secrets.env is already file-permission protected
- Do not delete or rename any existing routes or views
