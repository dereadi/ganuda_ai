# KB-FLASK-ROUTE-REGISTRATION-001: Flask Routes Must Be Defined Before app.run()

**Created**: 2025-12-10
**Category**: Bug Fix / Development
**Severity**: High
**Component**: SAG Unified Interface (app.py)

---

## Summary

Flask route decorators (`@app.route()`) must be defined BEFORE `app.run()` is called. Routes added after `app.run()` will never be registered, resulting in 404 errors.

---

## Symptom

- New API endpoint returns 404 "Not found"
- No errors in Flask logs during startup
- Route decorator is present in code
- Endpoint appears correct in code review

---

## Root Cause

Flask's `app.run()` starts the WSGI server and begins handling requests. Any route decorators after this line are never executed during normal operation. The Python code after `app.run()` only executes after the server stops.

**Bad Pattern:**
```python
@app.route('/api/existing')
def existing_endpoint():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)

# WRONG - This route is never registered!
@app.route('/api/new-endpoint')
def new_endpoint():
    return jsonify({'data': 'never reached'})
```

**Correct Pattern:**
```python
@app.route('/api/existing')
def existing_endpoint():
    return jsonify({'status': 'ok'})

# CORRECT - Routes before app.run()
@app.route('/api/new-endpoint')
def new_endpoint():
    return jsonify({'data': 'works correctly'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)
```

---

## Resolution

When adding new endpoints to an existing Flask app:

1. **Identify the `if __name__ == '__main__':` block**
2. **Add new routes BEFORE that block**
3. **Restart the Flask application**

### Fix Command Used (SAG app.py)

```bash
# Move endpoint code (lines 1878-1967) to before app.run() block (line 1852)
head -n 1851 app.py.backup > app.py.fixed && \
sed -n '1878,1967p' app.py.backup >> app.py.fixed && \
echo '' >> app.py.fixed && \
sed -n '1852,1877p' app.py.backup >> app.py.fixed && \
mv app.py.fixed app.py
```

---

## Prevention

1. **Code Review Checklist**: Verify new routes are above `if __name__ == '__main__':`
2. **Jr Instructions**: Always specify insertion point relative to main block
3. **Testing**: Always verify new endpoints with curl after deployment

---

## Related Incident

- **Date**: 2025-12-10
- **Component**: `/api/awareness/orthogonal` endpoint in SAG Dashboard
- **Resolution Time**: ~30 minutes
- **Impact**: New orthogonal pulse endpoint was returning 404

---

**For Seven Generations**

*Document learnings to prevent repeated mistakes.*
