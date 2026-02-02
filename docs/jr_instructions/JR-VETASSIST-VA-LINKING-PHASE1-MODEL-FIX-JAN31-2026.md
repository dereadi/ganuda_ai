# JR-VETASSIST-VA-LINKING-PHASE1-MODEL-FIX-JAN31-2026

## Metadata
- **Priority:** P0
- **Jr Type:** Engineering
- **Target Node:** sasass2 (192.168.132.200)
- **Category:** VetAssist — VA Account Linking Phase 1 (Database + Model)
- **Depends On:** None
- **Council Vote:** ULTRATHINK-EXECUTOR-SEARCH-REPLACE-ARCHITECTURE-JAN31-2026

## Objective

Add VA account linking columns to the `users` table and fix the SQLAlchemy model. A previous Jr task incorrectly placed `va_icn` and `va_linked_at` on the `UserSession` class — this task moves them to the correct `User` class and adds them to the database.

## Step 1: SQL Migration — Add Columns to users Table

```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
ALTER TABLE users ADD COLUMN IF NOT EXISTS va_icn VARCHAR(50) UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS va_linked_at TIMESTAMPTZ;
"
```

```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'users' AND column_name IN ('va_icn', 'va_linked_at')
ORDER BY column_name;
"
```

## Step 2: Add va_icn and va_linked_at to User Class

**File:** `/ganuda/vetassist/backend/app/models/user.py`

<<<<<<< SEARCH
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"
=======
    # VA Account Linking
    va_icn = Column(String(50), unique=True, nullable=True)
    va_linked_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"
>>>>>>> REPLACE

## Step 3: Add va_linked to User.to_dict()

**File:** `/ganuda/vetassist/backend/app/models/user.py`

<<<<<<< SEARCH
            "email_verified": self.email_verified,
            "is_active": self.is_active
        }
=======
            "email_verified": self.email_verified,
            "is_active": self.is_active,
            "va_linked": self.va_icn is not None,
            "va_linked_at": self.va_linked_at.isoformat() if self.va_linked_at else None
        }
>>>>>>> REPLACE

## Step 4: Remove Misplaced va_icn from UserSession

A previous Jr task incorrectly added these columns to UserSession. Remove them from the model.

**File:** `/ganuda/vetassist/backend/app/models/user.py`

<<<<<<< SEARCH
    def __repr__(self):
        return f"<UserSession {self.id} for user {self.user_id}>"

    # VA Account Linking
    va_icn = Column(String(50), unique=True, nullable=True)
    va_linked_at = Column(DateTime(timezone=True), nullable=True)
=======
    def __repr__(self):
        return f"<UserSession {self.id} for user {self.user_id}>"
>>>>>>> REPLACE

## Step 5: Verify Syntax

```bash
python3 -c "
import py_compile
try:
    py_compile.compile('/ganuda/vetassist/backend/app/models/user.py', doraise=True)
    print('PASS: user.py syntax valid')
except py_compile.PyCompileError as e:
    print(f'FAIL: {e}')
"
```

## Rollback

To undo the SQL migration, run manually on bluefin:
  ALTER TABLE users DROP COLUMN IF EXISTS va_icn;
  ALTER TABLE users DROP COLUMN IF EXISTS va_linked_at;

To undo the model changes, restore from the most recent backup:
  ls -la /ganuda/vetassist/backend/app/models/user.py.sr_backup_*
