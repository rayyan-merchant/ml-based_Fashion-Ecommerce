# app/routers/admins.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.database import get_db
from app.schemas.admins_schema import (
    AdminCreate, AdminLogin, TokenResponse, AdminOut, AdminMe, ChangePasswordRequest
)
from app.core.auth import (
    create_access_token,
    get_current_admin,
    verify_password,
    hash_password,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/admins", tags=["Admins"])


# ---------------------------
# Helpers
# ---------------------------
def _log_admin_action(db: Session, admin_id: int, action: str, details: Optional[dict] = None):
    """Write a record in niche_data.admin_activity_log (best-effort)."""
    try:
        details_json = text("to_jsonb(:d::text)")  # placeholder so we pass via params below
        sql = text("""
            INSERT INTO niche_data.admin_activity_log (admin_id, action, details, created_at)
            VALUES (:admin_id, :action, :details::jsonb, NOW())
        """)
        db.execute(sql, {"admin_id": admin_id, "action": action, "details": (details or {})})
    except Exception:
        # never fail the main operation because of logging
        pass


# ---------------------------
# Login (JSON) - returns JWT
# ---------------------------
@router.post("/login", response_model=TokenResponse)
def login(payload: AdminLogin, db: Session = Depends(get_db)):
    """
    JSON login endpoint: accepts username or email + password.
    - First tries passlib `verify_password` against stored hash.
    - If that fails or hash format unknown, falls back to DB-side crypt() check (legacy).
    On success: updates last_login_at and returns JWT.
    """
    ident = payload.username_or_email.strip()

    # 1) Try to fetch admin row
    row = db.execute(
        text("""
            SELECT admin_id, username, email, password_hash, created_at, last_login_at, is_active
            FROM niche_data.admins
            WHERE username = :ident OR email = :ident
            LIMIT 1
        """),
        {"ident": ident}
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # 2) Verify password locally (passlib). If that fails, attempt DB crypt() fallback.
    stored_hash = row["password_hash"]
    ok = False

    try:
        # preferred: passlib verification (handles bcrypt and other modern hashes)
        ok = verify_password(payload.password, stored_hash)
    except Exception:
        ok = False

    if not ok:
        # fallback to DB crypt() comparison (legacy stored using crypt)
        fallback = db.execute(
            text("""
                SELECT admin_id, username, email, created_at, last_login_at, is_active
                FROM niche_data.admins
                WHERE (username = :ident OR email = :ident)
                  AND password_hash = crypt(:pwd, password_hash)
                  AND is_active = TRUE
                LIMIT 1
            """),
            {"ident": ident, "pwd": payload.password}
        ).mappings().first()
        if fallback:
            ok = True
            row = fallback  # use the row from fallback (same data)

    if not ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not row["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin inactive")

    admin_id = row["admin_id"]

    # Update last_login_at
    db.execute(
        text("UPDATE niche_data.admins SET last_login_at = NOW() WHERE admin_id = :aid"),
        {"aid": admin_id}
    )
    db.commit()

    # Log login
    try:
        _log_admin_action(db, admin_id, "login", None)
    except Exception:
        pass

    # Create token with admin_id (will be converted to {"sub": str(admin_id), "type": "admin"})
    token = create_access_token(admin_id, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": token, "token_type": "bearer", "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES}


# ---------------------------
# Create admin (protected)
# ---------------------------
@router.post("/", response_model=AdminOut, status_code=status.HTTP_201_CREATED)
def create_admin(payload: AdminCreate, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """
    Create a new admin. Protected: requires an authenticated admin.
    Uses passlib hashing for new accounts.
    """
    # uniqueness check
    exists = db.execute(
        text("SELECT 1 FROM niche_data.admins WHERE username = :u OR email = :e LIMIT 1"),
        {"u": payload.username, "e": payload.email}
    ).scalar()

    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already exists")

    hashed = hash_password(payload.password)

    row = db.execute(
        text("""
            INSERT INTO niche_data.admins (username, email, password_hash, created_at, is_active)
            VALUES (:u, :e, :ph, NOW(), :active)
            RETURNING admin_id, username, email, created_at, last_login_at, is_active
        """),
        {"u": payload.username, "e": payload.email, "ph": hashed, "active": bool(payload.is_active)}
    ).mappings().first()

    db.commit()

    # log creation
    try:
        _log_admin_action(db, current_admin.admin_id, "create_admin", {"created_admin": row["admin_id"]})
    except Exception:
        pass

    return row


# ---------------------------
# List admins (protected)
# ---------------------------
@router.get("/", response_model=List[AdminOut])
def list_admins(db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    rows = db.execute(
        text("""
            SELECT admin_id, username, email, created_at, last_login_at, is_active
            FROM niche_data.admins
            ORDER BY admin_id
            LIMIT 1000
        """)
    ).mappings().all()
    return rows


# ---------------------------
# Get me (protected)
# ---------------------------
@router.get("/me", response_model=AdminMe)
def me(current_admin = Depends(get_current_admin)):
    """
    Get current admin info.
    current_admin is a SQLAlchemy Admin model, which will be converted to AdminMe Pydantic model.
    """
    # Convert SQLAlchemy Admin model to AdminMe Pydantic model
    return AdminMe(
        admin_id=current_admin.admin_id,
        username=current_admin.username,
        email=current_admin.email,
        last_login_at=current_admin.last_login_at,
        is_active=current_admin.is_active
    )


# ---------------------------
# Change password (protected)
# ---------------------------
@router.post("/change-password")
def change_password(payload: ChangePasswordRequest, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    # verify old password (try passlib then DB crypt fallback)
    ident = current_admin.username
    # first try passlib verify against stored hash
    stored = db.execute(text("SELECT password_hash FROM niche_data.admins WHERE admin_id = :aid"), {"aid": current_admin.admin_id}).scalar()
    if not stored:
        raise HTTPException(status_code=400, detail="Admin record missing")

    ok = verify_password(payload.old_password, stored)
    if not ok:
        # fallback DB crypt check
        chk = db.execute(
            text("""
                SELECT 1 FROM niche_data.admins
                WHERE admin_id = :aid AND password_hash = crypt(:pwd, password_hash)
            """),
            {"aid": current_admin.admin_id, "pwd": payload.old_password}
        ).scalar()
        ok = bool(chk)

    if not ok:
        raise HTTPException(status_code=400, detail="Old password incorrect")

    new_hashed = hash_password(payload.new_password)
    db.execute(
        text("UPDATE niche_data.admins SET password_hash = :ph WHERE admin_id = :aid"),
        {"ph": new_hashed, "aid": current_admin.admin_id}
    )
    db.commit()

    # Log change
    try:
        _log_admin_action(db, current_admin.admin_id, "change_password", None)
    except Exception:
        pass

    return {"detail": "Password changed successfully"}


# ---------------------------
# Simple admin activity logs view (protected)
# ---------------------------
@router.get("/logs")
def get_admin_logs(limit: int = 100, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    rows = db.execute(
        text("""
            SELECT log_id, admin_id, action, details, created_at
            FROM niche_data.admin_activity_log
            ORDER BY created_at DESC
            LIMIT :limit
        """),
        {"limit": limit}
    ).mappings().all()
    return rows
