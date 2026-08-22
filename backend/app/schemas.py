from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

from .models import ConsentStatus, UserRole


# ---------- Users ----------

from .models import ConsentStatus, UserRole  # update this import line

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
class UserCreate(BaseModel):
    name: str
    email: EmailStr


class UserOut(BaseModel):
    user_id: str
    name: str
    email: EmailStr
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ---------- Consent ----------

class ConsentCreate(BaseModel):
    user_id: str
    purpose: str
    data_type: str
    expires_at: Optional[datetime] = None
    # Optional raw consent text for the AI analyzer (Phase 11). If omitted,
    # the analyzer falls back to purpose + data_type.
    consent_text: Optional[str] = None


class ConsentActivate(BaseModel):
    blockchain_tx_hash: str


class ConsentOut(BaseModel):
    consent_id: str
    user_id: str
    purpose: str
    data_type: str
    status: ConsentStatus
    created_at: datetime
    revoked_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    blockchain_tx_hash: Optional[str] = None
    ai_risk: Optional[str] = None
    ai_reason: Optional[str] = None
    ai_recommendation: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- AI ----------

class AIAnalysisRequest(BaseModel):
    text: str


class AIAnalysisResponse(BaseModel):
    risk: str
    reason: str
    recommendation: str


# ---------- Audit ----------

class AccessLogCreate(BaseModel):
    consent_id: str
    accessor_id: str
    purpose: str


class AccessLogOut(BaseModel):
    access_id: str
    consent_id: str
    accessor_id: str
    accessed_at: datetime
    purpose: str
    blockchain_tx_hash: Optional[str] = None

    class Config:
        from_attributes = True
class AccessRequestIn(BaseModel):
    consent_id: str
    accessor_id: str
    requested_purpose: str
    requested_data_type: str


class AccessRequestOut(BaseModel):
    allowed: bool
    reason: str
    access_log: Optional[AccessLogOut] = None