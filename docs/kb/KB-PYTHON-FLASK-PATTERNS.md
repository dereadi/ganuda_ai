# KB-PYTHON-FLASK-PATTERNS: Python and Flask Coding Standards for Jr Agents

**Date:** 2025-12-06
**Author:** TPM (Command Post)
**Category:** Development Standards
**Audience:** IT Jr Agents, Dev Jr Agents
**Priority:** HIGH - Reference before code generation

---

## Purpose

This KB provides coding patterns and standards that Jr agents MUST follow when generating Python code for the Cherokee AI / Ganuda infrastructure.

---

## 1. Flask Route Patterns

### Standard API Endpoint Structure

```python
@app.route('/api/<resource>', methods=['GET'])
def get_resource():
    """Get all resources or filtered list."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM table_name ORDER BY created_at DESC LIMIT 100")
        results = cur.fetchall()
        return jsonify([dict(row) for row in results])
    except Exception as e:
        logger.error(f"Error fetching resource: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/<resource>/<id>', methods=['GET'])
def get_resource_by_id(id):
    """Get single resource by ID."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM table_name WHERE id = %s", (id,))
        result = cur.fetchone()
        if not result:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(dict(result))
    except Exception as e:
        logger.error(f"Error fetching resource {id}: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/<resource>', methods=['POST'])
def create_resource():
    """Create new resource."""
    conn = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        required = ['field1', 'field2']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({'error': f'Missing fields: {missing}'}), 400

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            INSERT INTO table_name (field1, field2, created_at)
            VALUES (%s, %s, NOW())
            RETURNING *
        """, (data['field1'], data['field2']))
        result = cur.fetchone()
        conn.commit()
        return jsonify(dict(result)), 201
    except Exception as e:
        logger.error(f"Error creating resource: {e}")
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/<resource>/<id>', methods=['PUT'])
def update_resource(id):
    """Update existing resource."""
    conn = None
    try:
        data = request.get_json()
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            UPDATE table_name
            SET field1 = %s, field2 = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING *
        """, (data.get('field1'), data.get('field2'), id))
        result = cur.fetchone()
        if not result:
            return jsonify({'error': 'Not found'}), 404
        conn.commit()
        return jsonify(dict(result))
    except Exception as e:
        logger.error(f"Error updating resource {id}: {e}")
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()
```

---

## 2. Database Connection Pattern

### Standard Connection Function

```python
import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'triad_federation',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

def get_db_connection():
    """Get database connection with RealDictCursor support."""
    return psycopg2.connect(**DB_CONFIG)
```

### Query with RealDictCursor (ALWAYS USE THIS)

```python
conn = get_db_connection()
cur = conn.cursor(cursor_factory=RealDictCursor)
cur.execute("SELECT * FROM table")
rows = cur.fetchall()
# rows is now list of dict-like objects
for row in rows:
    print(row['column_name'])  # Access by column name, not index!
```

### NEVER DO THIS (tuple index access)

```python
# BAD - causes "tuple index out of range" errors
cur.execute("SELECT * FROM table")
rows = cur.fetchall()
for row in rows:
    print(row[0])  # DON'T access by index!
```

---

## 3. Error Handling Pattern

```python
import logging

logger = logging.getLogger(__name__)

def safe_operation():
    """Template for safe database operations."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Your operations here
        cursor.execute("SELECT 1")
        result = cursor.fetchone()

        conn.commit()
        return result

    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
```

---

## 4. Flask HTML Tab Pattern

### Adding a New Tab to index.html

```html
<!-- In the nav section -->
<nav class="tab-nav">
    <!-- Existing tabs... -->
    <button class="tab-btn" data-tab="newtab">🆕 New Tab</button>
</nav>

<!-- Tab content section -->
<div id="newtab-tab" class="tab-content">
    <div class="tab-header">
        <h2>New Feature Title</h2>
        <button onclick="refreshNewTab()" class="refresh-btn">🔄 Refresh</button>
    </div>

    <div class="content-grid">
        <!-- Your content here -->
        <div id="newtab-data" class="data-container">
            Loading...
        </div>
    </div>
</div>
```

### JavaScript for Tab Data Loading

```javascript
// In unified.js or separate file

async function loadNewTabData() {
    try {
        const response = await fetch('/api/newtab/data');
        if (!response.ok) throw new Error('Failed to fetch data');
        const data = await response.json();
        renderNewTabData(data);
    } catch (error) {
        console.error('Error loading new tab data:', error);
        document.getElementById('newtab-data').innerHTML =
            '<div class="error">Failed to load data</div>';
    }
}

function renderNewTabData(data) {
    const container = document.getElementById('newtab-data');
    container.innerHTML = data.map(item => `
        <div class="data-card">
            <h3>${item.title}</h3>
            <p>${item.description}</p>
        </div>
    `).join('');
}

// Auto-refresh every 60 seconds
setInterval(loadNewTabData, 60000);

// Load on tab switch
document.querySelector('[data-tab="newtab"]').addEventListener('click', loadNewTabData);
```

---

## 5. Chart.js Integration Pattern

### Include Chart.js (air-gapped compatible)

```html
<!-- Local copy preferred for air-gapped -->
<script src="/static/js/chart.min.js"></script>
<!-- Fallback to CDN if online -->
<script>
    if (typeof Chart === 'undefined') {
        document.write('<script src="https://cdn.jsdelivr.net/npm/chart.js"><\/script>');
    }
</script>
```

### Standard Chart Creation

```javascript
function createLineChart(canvasId, labels, datasets) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets.map((ds, i) => ({
                label: ds.label,
                data: ds.data,
                borderColor: getColor(i),
                backgroundColor: getColor(i, 0.1),
                tension: 0.1,
                fill: true
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true }
            },
            plugins: {
                legend: { position: 'top' }
            }
        }
    });
}

function createBarChart(canvasId, labels, datasets) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets.map((ds, i) => ({
                label: ds.label,
                data: ds.data,
                backgroundColor: getColor(i, 0.7),
                borderColor: getColor(i),
                borderWidth: 1
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, stacked: true },
                x: { stacked: true }
            }
        }
    });
}

const COLORS = ['#4e79a7', '#f28e2c', '#e15759', '#76b7b2', '#59a14f', '#edc949'];
function getColor(index, alpha = 1) {
    const color = COLORS[index % COLORS.length];
    if (alpha === 1) return color;
    // Convert hex to rgba
    const r = parseInt(color.slice(1,3), 16);
    const g = parseInt(color.slice(3,5), 16);
    const b = parseInt(color.slice(5,7), 16);
    return `rgba(${r},${g},${b},${alpha})`;
}
```

---

## 6. Settings Management Pattern

### Settings Table Schema

```sql
CREATE TABLE IF NOT EXISTS sag_settings (
    setting_key VARCHAR(100) PRIMARY KEY,
    setting_value JSONB NOT NULL,
    description TEXT,
    category VARCHAR(50),
    editable BOOLEAN DEFAULT true,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by VARCHAR(50) DEFAULT 'system'
);
```

### Settings API Pattern

```python
@app.route('/api/settings', methods=['GET'])
def get_all_settings():
    """Get all settings grouped by category."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT setting_key, setting_value, description, category, editable
            FROM sag_settings
            ORDER BY category, setting_key
        """)
        rows = cur.fetchall()

        # Group by category
        grouped = {}
        for row in rows:
            cat = row['category'] or 'general'
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(dict(row))

        return jsonify(grouped)
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/settings/<key>', methods=['PUT'])
def update_setting(key):
    """Update a single setting."""
    conn = None
    try:
        data = request.get_json()
        if 'value' not in data:
            return jsonify({'error': 'No value provided'}), 400

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Check if editable
        cur.execute("SELECT editable FROM sag_settings WHERE setting_key = %s", (key,))
        row = cur.fetchone()
        if not row:
            return jsonify({'error': 'Setting not found'}), 404
        if not row['editable']:
            return jsonify({'error': 'Setting is not editable'}), 403

        # Update
        cur.execute("""
            UPDATE sag_settings
            SET setting_value = %s, updated_at = NOW(), updated_by = %s
            WHERE setting_key = %s
            RETURNING *
        """, (json.dumps(data['value']), data.get('user', 'api'), key))
        result = cur.fetchone()
        conn.commit()

        return jsonify(dict(result))
    except Exception as e:
        logger.error(f"Error updating setting {key}: {e}")
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()
```

---

## 7. Thermal Memory Integration Pattern

### Writing to Thermal Memory

```python
def write_to_thermal_memory(content: str, temperature: float, source: str, tags: list = None):
    """Write content to thermal memory."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            INSERT INTO triad_shared_memories (content, temperature, source_triad, tags)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (content, temperature, source, tags or []))
        result = cur.fetchone()
        conn.commit()
        return result['id']
    except Exception as e:
        logger.error(f"Error writing to thermal memory: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()
```

### Reading from Thermal Memory

```python
def read_thermal_memory(source: str = None, min_temp: float = 0, limit: int = 50):
    """Read from thermal memory with optional filters."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT id, content, temperature, source_triad, tags, created_at
            FROM triad_shared_memories
            WHERE temperature >= %s
        """
        params = [min_temp]

        if source:
            query += " AND source_triad = %s"
            params.append(source)

        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error reading thermal memory: {e}")
        return []
    finally:
        if conn:
            conn.close()
```

---

## 8. File Structure Standards

### SAG Unified Interface Directory

```
/ganuda/home/dereadi/sag_unified_interface/
├── app.py                    # Main Flask application
├── templates/
│   └── index.html           # Main HTML template
├── static/
│   ├── css/
│   │   └── styles.css       # Main stylesheet
│   └── js/
│       ├── unified.js       # Main JavaScript
│       ├── chart.min.js     # Chart.js library (local)
│       ├── dashboard.js     # Performance charts
│       ├── settings.js      # Settings management
│       └── console.js       # Command console
├── event_manager.py         # Event handling
├── thermal_memory_client.py # Thermal memory access
├── kanban_integration.py    # Kanban board integration
├── fara_integration.py      # FARA integration
└── settings_manager.py      # Settings CRUD
```

---

## 9. Common Mistakes to AVOID

### 1. Don't use tuple indexing with database results
```python
# WRONG
row[0], row[1]

# RIGHT
row['id'], row['name']
```

### 2. Don't forget to close connections
```python
# WRONG
conn = get_db_connection()
cur = conn.cursor()
cur.execute("SELECT 1")
return cur.fetchone()  # Connection leak!

# RIGHT - use try/finally
conn = None
try:
    conn = get_db_connection()
    # ...
finally:
    if conn:
        conn.close()
```

### 3. Don't hardcode database credentials in multiple files
```python
# WRONG - credentials scattered everywhere
conn = psycopg2.connect(host='192.168.132.222', password='xxx')

# RIGHT - use central config
from config import DB_CONFIG
conn = psycopg2.connect(**DB_CONFIG)
```

### 4. Don't forget CORS for API endpoints accessed by frontend
```python
from flask_cors import CORS
app = Flask(__name__)
CORS(app)  # Enable for all routes
```

### 5. Don't return Python objects directly from Flask
```python
# WRONG
return rows  # Can't serialize cursor results

# RIGHT
return jsonify([dict(row) for row in rows])
```

---

## 10. Testing Pattern

### Quick API Test

```python
def test_api_endpoint():
    """Test template for API endpoints."""
    import requests

    base_url = "http://192.168.132.223:4000"

    # Test GET
    response = requests.get(f"{base_url}/api/resource")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Test POST
    response = requests.post(f"{base_url}/api/resource",
                            json={'field1': 'value1'})
    assert response.status_code in [200, 201]

    print("All tests passed!")

if __name__ == '__main__':
    test_api_endpoint()
```

---

**END OF KB-PYTHON-FLASK-PATTERNS**

Jr agents should load and reference this document before generating any Python/Flask code for SAG or related systems.
