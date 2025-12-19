# JR INSTRUCTIONS: Build Email Intelligence UI for SAG Dashboard
## Priority: 1 (User Waiting)
## December 17, 2025

### OBJECTIVE
Build the Email Intelligence tab in SAG Unified Interface at http://192.168.132.223:4000/ to display job emails, classifications, and pipeline status.

---

## BACKGROUND

**Current State:**
- SAG UI at `/ganuda/home/dereadi/sag_unified_interface/`
- Email nav item exists, but content is empty placeholder
- Email data in `triad_federation.emails` table on bluefin (192.168.132.222)
- Job classifications: offer, interview, next_steps, application, recruiter, rejection

**Database Schema (triad_federation.emails):**
- id, message_id, subject, from_address, body_text
- date_received, job_classification, job_company, job_position
- action_required, thermal_temp, priority_score

---

## TASK 1: Add Email API Endpoint to SAG Backend

**File:** `/ganuda/home/dereadi/sag_unified_interface/app.py`

**Add these imports at top:**
```python
from datetime import datetime, timedelta
```

**Add these endpoints:**

```python
@app.route('/api/emails/stats')
def email_stats():
    """Get email classification statistics."""
    try:
        conn = get_db_connection('triad_federation')
        cur = conn.cursor()
        cur.execute('''
            SELECT
                job_classification,
                COUNT(*) as count
            FROM emails
            WHERE job_classification IS NOT NULL
            GROUP BY job_classification
            ORDER BY count DESC
        ''')
        stats = {row[0]: row[1] for row in cur.fetchall()}

        cur.execute('SELECT COUNT(*) FROM emails WHERE action_required = true')
        action_required = cur.fetchone()[0]

        cur.execute('SELECT COUNT(*) FROM emails WHERE date_received > NOW() - INTERVAL \'24 hours\'')
        last_24h = cur.fetchone()[0]

        cur.close()
        conn.close()

        return jsonify({
            'classifications': stats,
            'action_required': action_required,
            'last_24h': last_24h,
            'total': sum(stats.values())
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/emails/list')
def email_list():
    """Get list of job emails with optional filtering."""
    classification = request.args.get('classification', None)
    limit = request.args.get('limit', 50, type=int)

    try:
        conn = get_db_connection('triad_federation')
        cur = conn.cursor()

        query = '''
            SELECT id, message_id, subject, from_address, date_received,
                   job_classification, job_company, job_position, action_required,
                   LEFT(body_text, 200) as snippet
            FROM emails
            WHERE job_classification IS NOT NULL
        '''
        params = []

        if classification:
            query += ' AND job_classification = %s'
            params.append(classification)

        query += ' ORDER BY date_received DESC LIMIT %s'
        params.append(limit)

        cur.execute(query, params)
        columns = ['id', 'message_id', 'subject', 'from_address', 'date_received',
                   'job_classification', 'job_company', 'job_position', 'action_required', 'snippet']
        emails = [dict(zip(columns, row)) for row in cur.fetchall()]

        # Convert datetime to string
        for email in emails:
            if email['date_received']:
                email['date_received'] = email['date_received'].isoformat()

        cur.close()
        conn.close()

        return jsonify({'emails': emails})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/emails/pipeline')
def email_pipeline():
    """Get job pipeline view - applications in progress."""
    try:
        conn = get_db_connection('triad_federation')
        cur = conn.cursor()

        # Get recent by classification for pipeline view
        cur.execute('''
            SELECT job_classification, job_company, job_position, subject,
                   date_received, from_address
            FROM emails
            WHERE job_classification IN ('offer', 'interview', 'next_steps', 'application')
              AND date_received > NOW() - INTERVAL '30 days'
            ORDER BY
                CASE job_classification
                    WHEN 'offer' THEN 1
                    WHEN 'interview' THEN 2
                    WHEN 'next_steps' THEN 3
                    WHEN 'application' THEN 4
                END,
                date_received DESC
        ''')

        columns = ['classification', 'company', 'position', 'subject', 'date', 'from']
        pipeline = [dict(zip(columns, row)) for row in cur.fetchall()]

        for item in pipeline:
            if item['date']:
                item['date'] = item['date'].isoformat()

        cur.close()
        conn.close()

        return jsonify({'pipeline': pipeline})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**Add helper function if not exists:**
```python
def get_db_connection(dbname='triad_federation'):
    """Get database connection."""
    import psycopg2
    return psycopg2.connect(
        host='192.168.132.222',
        database=dbname,
        user='claude',
        password='jawaseatlasers2'
    )
```

---

## TASK 2: Add Email UI JavaScript

**File:** `/ganuda/home/dereadi/sag_unified_interface/static/js/unified.js`

**Add at end of file:**

```javascript
// ============================================================
// EMAIL INTELLIGENCE MODULE
// ============================================================

const EmailIntelligence = {
    classificationEmoji: {
        'offer': '💰',
        'interview': '📅',
        'next_steps': '➡️',
        'application': '📝',
        'recruiter': '👤',
        'rejection': '❌'
    },

    classificationColors: {
        'offer': '#22c55e',
        'interview': '#3b82f6',
        'next_steps': '#f59e0b',
        'application': '#8b5cf6',
        'recruiter': '#06b6d4',
        'rejection': '#ef4444'
    },

    async loadStats() {
        try {
            const res = await fetch('/api/emails/stats');
            const data = await res.json();
            return data;
        } catch (e) {
            console.error('Failed to load email stats:', e);
            return null;
        }
    },

    async loadEmails(classification = null) {
        try {
            let url = '/api/emails/list?limit=50';
            if (classification) url += '&classification=' + classification;
            const res = await fetch(url);
            const data = await res.json();
            return data.emails || [];
        } catch (e) {
            console.error('Failed to load emails:', e);
            return [];
        }
    },

    async loadPipeline() {
        try {
            const res = await fetch('/api/emails/pipeline');
            const data = await res.json();
            return data.pipeline || [];
        } catch (e) {
            console.error('Failed to load pipeline:', e);
            return [];
        }
    },

    renderStatsCards(stats) {
        if (!stats) return '<p>Failed to load stats</p>';

        const cards = [
            { label: 'Last 24h', value: stats.last_24h || 0, color: '#3b82f6' },
            { label: 'Action Required', value: stats.action_required || 0, color: '#ef4444' },
            { label: 'Offers', value: stats.classifications?.offer || 0, color: '#22c55e' },
            { label: 'Interviews', value: stats.classifications?.interview || 0, color: '#3b82f6' },
            { label: 'In Progress', value: stats.classifications?.next_steps || 0, color: '#f59e0b' },
            { label: 'Applications', value: stats.classifications?.application || 0, color: '#8b5cf6' }
        ];

        return `
            <div class="email-stats-grid">
                ${cards.map(c => `
                    <div class="stat-card" style="border-left: 4px solid ${c.color}">
                        <div class="stat-value">${c.value}</div>
                        <div class="stat-label">${c.label}</div>
                    </div>
                `).join('')}
            </div>
        `;
    },

    renderPipeline(pipeline) {
        if (!pipeline || pipeline.length === 0) {
            return '<p class="empty-state">No active job pipeline items</p>';
        }

        const grouped = {};
        pipeline.forEach(item => {
            const cls = item.classification;
            if (!grouped[cls]) grouped[cls] = [];
            grouped[cls].push(item);
        });

        const order = ['offer', 'interview', 'next_steps', 'application'];

        return `
            <div class="pipeline-container">
                ${order.map(cls => {
                    const items = grouped[cls] || [];
                    const emoji = this.classificationEmoji[cls];
                    const color = this.classificationColors[cls];
                    return `
                        <div class="pipeline-column">
                            <div class="pipeline-header" style="background: ${color}">
                                ${emoji} ${cls.replace('_', ' ').toUpperCase()} (${items.length})
                            </div>
                            <div class="pipeline-items">
                                ${items.slice(0, 5).map(item => `
                                    <div class="pipeline-card">
                                        <div class="pipeline-company">${item.company || 'Unknown Company'}</div>
                                        <div class="pipeline-position">${item.position || item.subject?.substring(0, 40) || 'Unknown'}</div>
                                        <div class="pipeline-date">${item.date ? new Date(item.date).toLocaleDateString() : ''}</div>
                                    </div>
                                `).join('')}
                                ${items.length > 5 ? `<div class="pipeline-more">+${items.length - 5} more</div>` : ''}
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    },

    renderEmailList(emails, filter = null) {
        if (!emails || emails.length === 0) {
            return '<p class="empty-state">No emails found</p>';
        }

        return `
            <div class="email-filters">
                <button class="filter-btn ${!filter ? 'active' : ''}" onclick="EmailIntelligence.filterEmails(null)">All</button>
                ${Object.keys(this.classificationEmoji).map(cls => `
                    <button class="filter-btn ${filter === cls ? 'active' : ''}" onclick="EmailIntelligence.filterEmails('${cls}')">
                        ${this.classificationEmoji[cls]} ${cls.replace('_', ' ')}
                    </button>
                `).join('')}
            </div>
            <div class="email-list">
                ${emails.map(email => `
                    <div class="email-row" onclick="EmailIntelligence.openEmail('${email.message_id}')">
                        <div class="email-classification" style="background: ${this.classificationColors[email.job_classification] || '#666'}">
                            ${this.classificationEmoji[email.job_classification] || '📧'}
                        </div>
                        <div class="email-content">
                            <div class="email-subject">${email.subject || 'No Subject'}</div>
                            <div class="email-from">${email.from_address || 'Unknown'}</div>
                            <div class="email-snippet">${email.snippet || ''}</div>
                        </div>
                        <div class="email-meta">
                            <div class="email-date">${email.date_received ? new Date(email.date_received).toLocaleDateString() : ''}</div>
                            ${email.job_company ? `<div class="email-company">${email.job_company}</div>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    },

    async filterEmails(classification) {
        const emails = await this.loadEmails(classification);
        document.getElementById('email-list-container').innerHTML = this.renderEmailList(emails, classification);
    },

    openEmail(messageId) {
        if (messageId) {
            window.open(`https://mail.google.com/mail/u/0/#search/rfc822msgid:${messageId}`, '_blank');
        }
    },

    async render() {
        const container = document.getElementById('email-content');
        if (!container) return;

        container.innerHTML = '<p>Loading email intelligence...</p>';

        const [stats, pipeline, emails] = await Promise.all([
            this.loadStats(),
            this.loadPipeline(),
            this.loadEmails()
        ]);

        container.innerHTML = `
            <div class="email-intelligence">
                <section class="email-section">
                    <h3>📊 Overview</h3>
                    ${this.renderStatsCards(stats)}
                </section>

                <section class="email-section">
                    <h3>🎯 Job Pipeline</h3>
                    ${this.renderPipeline(pipeline)}
                </section>

                <section class="email-section">
                    <h3>📬 Recent Job Emails</h3>
                    <div id="email-list-container">
                        ${this.renderEmailList(emails)}
                    </div>
                </section>
            </div>
        `;
    }
};

// Hook into view switching
document.addEventListener('DOMContentLoaded', () => {
    const emailNavItem = document.querySelector('[data-view="email"]');
    if (emailNavItem) {
        emailNavItem.addEventListener('click', () => {
            EmailIntelligence.render();
        });
    }
});
```

---

## TASK 3: Add Email CSS Styles

**File:** `/ganuda/home/dereadi/sag_unified_interface/static/css/unified.css`

**Add at end of file:**

```css
/* ============================================================
   EMAIL INTELLIGENCE STYLES
   ============================================================ */

.email-intelligence {
    padding: 20px;
}

.email-section {
    margin-bottom: 30px;
}

.email-section h3 {
    margin-bottom: 15px;
    color: var(--color-text);
    font-size: 1.2rem;
}

/* Stats Grid */
.email-stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 15px;
}

.stat-card {
    background: var(--color-card-bg, #1e1e2e);
    padding: 20px;
    border-radius: 8px;
}

.stat-value {
    font-size: 2rem;
    font-weight: bold;
    color: var(--color-text);
}

.stat-label {
    font-size: 0.85rem;
    color: var(--color-text-muted, #888);
    margin-top: 5px;
}

/* Pipeline */
.pipeline-container {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 15px;
}

.pipeline-column {
    background: var(--color-card-bg, #1e1e2e);
    border-radius: 8px;
    overflow: hidden;
}

.pipeline-header {
    padding: 12px;
    color: white;
    font-weight: bold;
    font-size: 0.85rem;
    text-align: center;
}

.pipeline-items {
    padding: 10px;
    max-height: 300px;
    overflow-y: auto;
}

.pipeline-card {
    background: var(--color-bg, #12121a);
    padding: 12px;
    border-radius: 6px;
    margin-bottom: 8px;
}

.pipeline-company {
    font-weight: bold;
    color: var(--color-text);
    font-size: 0.9rem;
}

.pipeline-position {
    color: var(--color-text-muted, #888);
    font-size: 0.8rem;
    margin-top: 4px;
}

.pipeline-date {
    color: var(--color-text-muted, #666);
    font-size: 0.75rem;
    margin-top: 6px;
}

.pipeline-more {
    text-align: center;
    color: var(--color-text-muted);
    font-size: 0.8rem;
    padding: 8px;
}

/* Email Filters */
.email-filters {
    display: flex;
    gap: 8px;
    margin-bottom: 15px;
    flex-wrap: wrap;
}

.filter-btn {
    padding: 8px 16px;
    border: 1px solid var(--color-border, #333);
    background: var(--color-card-bg, #1e1e2e);
    color: var(--color-text);
    border-radius: 20px;
    cursor: pointer;
    font-size: 0.85rem;
    transition: all 0.2s;
}

.filter-btn:hover {
    background: var(--color-hover, #2a2a3e);
}

.filter-btn.active {
    background: var(--color-primary, #3b82f6);
    border-color: var(--color-primary, #3b82f6);
}

/* Email List */
.email-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.email-row {
    display: flex;
    align-items: center;
    gap: 15px;
    padding: 15px;
    background: var(--color-card-bg, #1e1e2e);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
}

.email-row:hover {
    background: var(--color-hover, #2a2a3e);
    transform: translateX(4px);
}

.email-classification {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    flex-shrink: 0;
}

.email-content {
    flex: 1;
    min-width: 0;
}

.email-subject {
    font-weight: 500;
    color: var(--color-text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.email-from {
    font-size: 0.85rem;
    color: var(--color-text-muted, #888);
    margin-top: 4px;
}

.email-snippet {
    font-size: 0.8rem;
    color: var(--color-text-muted, #666);
    margin-top: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.email-meta {
    text-align: right;
    flex-shrink: 0;
}

.email-date {
    font-size: 0.8rem;
    color: var(--color-text-muted, #888);
}

.email-company {
    font-size: 0.75rem;
    color: var(--color-primary, #3b82f6);
    margin-top: 4px;
}

.empty-state {
    color: var(--color-text-muted, #666);
    text-align: center;
    padding: 40px;
}

/* Responsive */
@media (max-width: 900px) {
    .pipeline-container {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 600px) {
    .pipeline-container {
        grid-template-columns: 1fr;
    }

    .email-row {
        flex-wrap: wrap;
    }

    .email-meta {
        width: 100%;
        text-align: left;
        margin-top: 10px;
    }
}
```

---

## TASK 4: Restart SAG UI Service

```bash
# Find and restart the SAG UI process
cd /ganuda/home/dereadi/sag_unified_interface
pkill -f "python.*app.py" || true
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install psycopg2-binary -q
nohup python3 app.py > /tmp/sag_ui.log 2>&1 &
sleep 2
curl -s http://localhost:4000/api/emails/stats | head -20
```

---

## VERIFICATION

1. Open http://192.168.132.223:4000/
2. Click "Email" in the sidebar
3. Should see:
   - Stats cards (Last 24h, Action Required, Offers, Interviews, etc.)
   - Pipeline view with 4 columns (Offers, Interviews, Next Steps, Applications)
   - Email list with filter buttons
4. Click any email row → opens Gmail in new tab

---

## SUCCESS CRITERIA

1. Email tab loads without errors
2. Stats display correctly from database
3. Pipeline shows job applications by stage
4. Email list is filterable by classification
5. Clicking email opens Gmail link

---

*Jr Instructions issued: December 17, 2025*
*For Seven Generations - Cherokee AI Federation*
