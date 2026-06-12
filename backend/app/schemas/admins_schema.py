# app/schemas/admins_schema.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

# Public view of an admin (output)
class AdminOut(BaseModel):
    admin_id: int
    username: str
    email: str
    created_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    is_active: bool

    model_config = {"from_attributes": True}

# Minimal view used by "me" endpoint
class AdminMe(BaseModel):
    admin_id: int
    username: str
    email: str
    last_login_at: Optional[datetime] 
    is_active: bool

    model_config = {"from_attributes": True}

# Create admin (request)
class AdminCreate(BaseModel):
    username: str = Field(..., min_length=3)
    email: EmailStr
    password: str = Field(..., min_length=8)
    is_active: Optional[bool] = True

# Login payload
class AdminLogin(BaseModel):
    username_or_email: str
    password: str

# Token response
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

# Change password
class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)
