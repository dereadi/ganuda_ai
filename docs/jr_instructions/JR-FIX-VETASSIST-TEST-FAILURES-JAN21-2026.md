# JR Instruction: Fix VetAssist Test Failures
## Task ID: TEST-FIX-001
## Priority: P1
## Target: bluefin

---

## Objective

Fix 1 failing test and 14 test errors in VetAssist backend test suite.

---

## Current State

Test suite results:
- **55 passed**
- **1 failed**: `test_config.py::TestConfigValidation::test_secret_key_required`
- **14 errors**: All in `test_auth_endpoints.py` (UUID/SQLite incompatibility)

---

## Issue 1: test_secret_key_required (FAILED)

### Problem

Test deletes `SECRET_KEY` from `os.environ`, but pydantic-settings still reads from `.env` file:

```python
def test_secret_key_required(self):
    """Test that SECRET_KEY is required"""
    # Remove SECRET_KEY
    if "SECRET_KEY" in os.environ:
        del os.environ["SECRET_KEY"]

    # Should raise validation error - BUT DOESN'T!
    # Because pydantic-settings reads from .env file
    with pytest.raises(ValidationError):
        from app.core.config import Settings
        Settings()  # Still works - reads from .env!
```

### Root Cause

`.env` file contains `SECRET_KEY`:
```
SECRET_KEY=c156f6c2fd44432f727251b8ea9e5ccf0c0ad34752cdcadc56968644bf29b64f
```

### Fix

Update test to disable `.env` file reading:

```python
def test_secret_key_required(self):
    """Test that SECRET_KEY is required"""
    import os
    from pydantic import ValidationError

    # Save original
    original_key = os.environ.get("SECRET_KEY")

    # Remove SECRET_KEY from environment
    if "SECRET_KEY" in os.environ:
        del os.environ["SECRET_KEY"]

    try:
        # Create Settings with .env file disabled
        from app.core.config import Settings
        with pytest.raises(ValidationError):
            Settings(_env_file=None)  # <-- KEY FIX: Disable .env reading
    finally:
        # Restore
        if original_key:
            os.environ["SECRET_KEY"] = original_key
```

---

## Issue 2: 14 Auth Endpoint Errors (UUID/SQLite)

### Problem

All 14 tests in `test_auth_endpoints.py` fail with:
```
sqlalchemy.exc.CompileError: (in table 'educational_content', column 'id'):
Compiler ... can't render element of type UUID
```

### Root Cause

Models use PostgreSQL-specific `UUID` type, but tests use SQLite in-memory database which doesn't support UUID.

From `app/models/content.py`:
```python
from sqlalchemy import Column, UUID, String, Text
id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
```

SQLite doesn't have native UUID support.

### Fix Options

**Option A: Use Portable UUID Type (Recommended)**

Update models to use UUID with `as_uuid=True` and string fallback:

```python
# In app/models/content.py
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid

# Portable UUID - works with both PostgreSQL and SQLite
class PortableUUID(TypeDecorator):
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return uuid.UUID(value)

# Use in model
id = Column(PortableUUID(), primary_key=True, default=uuid.uuid4)
```

**Option B: Use PostgreSQL for Tests**

Update `conftest.py` to use PostgreSQL test database instead of SQLite:

```python
# tests/conftest.py
TEST_DATABASE_URL = "postgresql://vetassist_test:password@localhost:5432/vetassist_test"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL)
    # ... rest of setup
```

**Option C: Conditional UUID Type**

Use different types based on database:

```python
from sqlalchemy import Column, String, event
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

def get_uuid_type():
    # Use String for SQLite, UUID for PostgreSQL
    return String(36)  # Works everywhere
```

### Recommended Approach

**Option A** is recommended because:
1. Tests run faster with SQLite in-memory
2. No additional PostgreSQL test database needed
3. Models remain portable
4. Single code path for production and tests

---

## Implementation Steps

### Step 1: Fix test_config.py

Edit `/ganuda/vetassist/backend/tests/test_config.py`:

```python
def test_secret_key_required(self):
    """Test that SECRET_KEY is required"""
    original_key = os.environ.get("SECRET_KEY")

    if "SECRET_KEY" in os.environ:
        del os.environ["SECRET_KEY"]

    try:
        from app.core.config import Settings
        with pytest.raises(ValidationError):
            Settings(_env_file=None)  # Disable .env file reading
    finally:
        if original_key:
            os.environ["SECRET_KEY"] = original_key
```

### Step 2: Create PortableUUID Type

Create `/ganuda/vetassist/backend/app/core/types.py`:

```python
"""Custom SQLAlchemy types for cross-database compatibility"""
from sqlalchemy import TypeDecorator, String
import uuid

class PortableUUID(TypeDecorator):
    """UUID type that works with both PostgreSQL and SQLite"""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)
```

### Step 3: Update Models

Update models that use UUID:
- `app/models/content.py`
- `app/models/user.py`
- Any other model with UUID columns

Replace:
```python
from sqlalchemy import UUID
id = Column(UUID, primary_key=True, default=uuid.uuid4)
```

With:
```python
from app.core.types import PortableUUID
id = Column(PortableUUID(), primary_key=True, default=uuid.uuid4)
```

### Step 4: Run Tests

```bash
cd /ganuda/vetassist/backend
source venv/bin/activate
python -m pytest tests/ -v --no-cov
```

Expected result: 56 passed, 0 failed, 0 errors

---

## Verification

```bash
# Run specific failing test
python -m pytest tests/test_config.py::TestConfigValidation::test_secret_key_required -v --no-cov

# Run auth endpoint tests
python -m pytest tests/test_auth_endpoints.py -v --no-cov

# Run full suite
python -m pytest tests/ -v
```

---

## Time Estimate

- Issue 1 (config test): 15 minutes
- Issue 2 (UUID types): 45 minutes
- Testing: 15 minutes
- **Total: ~75 minutes**

---

*Cherokee AI Federation - VetAssist Test Suite Hardening*
