# app/core/auth.py

import os
from datetime import datetime, timedelta
from typing import Any, Dict, Literal, Optional, Union

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models.admins import Admin
from app.db.models.customers import Customer


# ============================================================
#  CONFIG
# ============================================================

JWT_SECRET = os.getenv("JWT_SECRET", os.getenv("SECRET_KEY", "supersecret-key-change-in-prod"))
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================
#  SECURITY SCHEME (Swagger uses this → shows single Bearer box)
# ============================================================

auth_scheme = HTTPBearer(
    scheme_name="JWTBearer",
    description="Paste the JWT issued by the admin or customer login endpoints.",
)


# ============================================================
#  PASSWORD HASHING
# ============================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================
#  JWT CREATION
# ============================================================

def create_access_token(
    data: Union[Dict[str, Any], int, str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Creates a JWT token.
    Accepts either:
    - A dict → e.g. {"sub": "9", "type": "admin"}
    - An int/str (admin_id) → will create {"sub": str(admin_id), "type": "admin"}
    """
    if isinstance(data, (int, str)):
        # If admin_id is passed directly, create the payload
        to_encode = {"sub": str(data), "type": "admin"}
    else:
        # If dict is passed, use it (but ensure type is set)
        to_encode = data.copy()
        if "type" not in to_encode:
            to_encode["type"] = "admin"
    
    now = datetime.utcnow()

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"iat": now, "exp": expire})

    encoded = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded


# ============================================================
#  JWT DECODING
# ============================================================

def decode_access_token(token: str) -> dict:
    """
    Decodes the JWT token and returns its payload.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================
#  CURRENT ADMIN DEPENDENCY
# ============================================================

def _validate_subject(subject: Any) -> str:
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return str(subject)


def _get_admin_by_id(admin_id: str, db: Session) -> Admin:
    try:
        admin_id_int = int(admin_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: subject must be integer",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch admin from DB
    admin = db.query(Admin).filter(Admin.admin_id == admin_id_int).first()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return admin


def _get_customer_by_id(customer_id: str, db: Session) -> Customer:
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Customer not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # if not customer.active:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Customer account is inactive",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )
    return customer


def get_current_user(
    credentials=Depends(auth_scheme),
    db: Session = Depends(get_db),
):
    """
    Resolve any authenticated user (admin or customer) from the JWT.
    Returns a dict containing the token type, raw subject and attached model.
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    token_type: Optional[Literal["admin", "customer"]] = payload.get("type")
    subject = _validate_subject(payload.get("sub"))

    if token_type == "admin":
        admin = _get_admin_by_id(subject, db)
        return {"type": "admin", "subject": subject, "admin": admin, "customer": None}

    if token_type == "customer":
        customer = _get_customer_by_id(subject, db)
        return {"type": "customer", "subject": subject, "admin": None, "customer": customer}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token type",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_admin(user=Depends(get_current_user)) -> Admin:
    """
    Dependency to ensure the bearer token belongs to an admin.
    """
    if user["type"] != "admin" or not user["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user["admin"]


def get_current_customer(user=Depends(get_current_user)) -> Customer:
    """
    Dependency to ensure the bearer token belongs to a customer.
    """
    if user["type"] != "customer" or not user["customer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account required",
        )
    return user["customer"]
