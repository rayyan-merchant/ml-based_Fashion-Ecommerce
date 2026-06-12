# dependencies.py - Admin Authorization (Compatibility Layer)
# This file provides AdminResponse Pydantic model for backward compatibility
# It uses core/auth.py internally for actual authentication

from fastapi import Depends
from pydantic import BaseModel
from app.core.auth import get_current_admin as _get_current_admin_from_core
from app.db.models.admins import Admin

# Pydantic Models for backward compatibility
class AdminLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class AdminResponse(BaseModel):
    admin_id: int
    username: str
    email: str
    is_active: bool

# Re-export create_access_token from core/auth for backward compatibility
from app.core.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

# Get Current Admin - converts Admin model to AdminResponse for backward compatibility
def get_current_admin(admin: Admin = Depends(_get_current_admin_from_core)) -> AdminResponse:
    """
    Wrapper around core.auth.get_current_admin that returns AdminResponse Pydantic model
    instead of SQLAlchemy Admin model. This maintains backward compatibility with routers
    that expect AdminResponse.
    """
    return AdminResponse(
        admin_id=admin.admin_id,
        username=admin.username,
        email=admin.email,
        is_active=admin.is_active
    )