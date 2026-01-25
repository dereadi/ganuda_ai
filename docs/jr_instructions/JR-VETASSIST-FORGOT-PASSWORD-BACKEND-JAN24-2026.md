# Jr Instruction: VetAssist Forgot Password - Backend

**Task ID:** VETASSIST-FORGOT-PWD-BACKEND
**Priority:** P2
**Date:** January 24, 2026
**Phase:** Forgot Password (1 of 2)

## Objective

Add forgot password and reset password API endpoints.

## Files to Modify (2 files)

1. `/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py`
2. `/ganuda/vetassist/backend/app/services/auth_service.py`

## Required Changes

### 1. auth.py - Add forgot/reset password endpoints

Add at bottom of `/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py`:

```python
from pydantic import EmailStr
import secrets

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Request a password reset email.

    Always returns success to prevent email enumeration.
    """
    # Check if user exists (but don't reveal this to client)
    user = AuthService.get_user_by_email(db, data.email)

    if user:
        # Generate reset token
        reset_token = AuthService.create_password_reset_token(db, user)

        # Send email (async in production)
        # TODO: Implement email sending
        # For now, log the token for testing
        import logging
        logging.info(f"Password reset token for {data.email}: {reset_token}")

    # Always return success to prevent enumeration
    return MessageResponse(
        message="If an account exists with that email, you will receive a password reset link."
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using token from email.
    """
    # Validate token and get user
    user = AuthService.validate_reset_token(db, data.token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Validate new password strength
    from app.core.security import validate_password_strength
    is_valid, error = validate_password_strength(data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    # Update password
    AuthService.reset_password(db, user, data.new_password)

    # Invalidate the reset token
    AuthService.invalidate_reset_token(db, data.token)

    return MessageResponse(message="Password has been reset successfully. You can now login.")
```

### 2. auth_service.py - Add reset token methods

Add to `/ganuda/vetassist/backend/app/services/auth_service.py`:

```python
import secrets
from datetime import datetime, timedelta
from app.core.security import hash_password

class AuthService:
    # ... existing methods ...

    @staticmethod
    def get_user_by_email(db: Session, email: str):
        """Get user by email address"""
        from app.models.user import User
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create_password_reset_token(db: Session, user) -> str:
        """Create a password reset token (expires in 1 hour)"""
        from app.models.user import PasswordResetToken

        # Invalidate any existing tokens for this user
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id
        ).delete()

        # Create new token
        token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.add(reset_token)
        db.commit()

        return token

    @staticmethod
    def validate_reset_token(db: Session, token: str):
        """Validate reset token and return user if valid"""
        from app.models.user import PasswordResetToken, User

        reset_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token,
            PasswordResetToken.expires_at > datetime.utcnow(),
            PasswordResetToken.used_at.is_(None)
        ).first()

        if not reset_token:
            return None

        return db.query(User).filter(User.id == reset_token.user_id).first()

    @staticmethod
    def reset_password(db: Session, user, new_password: str):
        """Update user's password"""
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.utcnow()
        db.commit()

    @staticmethod
    def invalidate_reset_token(db: Session, token: str):
        """Mark reset token as used"""
        from app.models.user import PasswordResetToken

        db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token
        ).update({"used_at": datetime.utcnow()})
        db.commit()
```

## Database Migration Note

This task assumes a `password_reset_tokens` table exists. If not, create it:

```sql
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES vetassist_users(id),
    token VARCHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_reset_tokens_token ON password_reset_tokens(token);
```

## Output

Generate both modified files completely.

## Success Criteria

- [ ] POST /auth/forgot-password endpoint works
- [ ] POST /auth/reset-password endpoint works
- [ ] Token expires after 1 hour
- [ ] Token can only be used once
- [ ] Password strength validated on reset
