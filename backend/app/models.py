import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Enum
from .database import Base


def generate_id():
    return uuid.uuid4().hex[:12]


class ConsentStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class UserRole(str, enum.Enum):
    DATA_PRINCIPAL = "data_principal"
    DATA_FIDUCIARY = "data_fiduciary"


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, default=generate_id)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.DATA_PRINCIPAL)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Consent(Base):
    __tablename__ = "consents"

    consent_id = Column(String, primary_key=True, default=generate_id)
    user_id = Column(String, nullable=False)
    purpose = Column(String, nullable=False)
    data_type = Column(String, nullable=False)
    status = Column(Enum(ConsentStatus), default=ConsentStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    # Time-bound validity per the PPT's Policy Plane (ACTIVE -> EXPIRED)
    expires_at = Column(DateTime, nullable=True)
    # Populated once Nirali's smart contract confirms the on-chain transaction
    blockchain_tx_hash = Column(String, nullable=True)
    # AI analysis result, generated at creation time (Phase 10/11)
    ai_risk = Column(String, nullable=True)
    ai_reason = Column(String, nullable=True)
    ai_recommendation = Column(String, nullable=True)


class AccessLog(Base):
    __tablename__ = "access_logs"

    access_id = Column(String, primary_key=True, default=generate_id)
    consent_id = Column(String, nullable=False)
    accessor_id = Column(String, nullable=False)
    accessed_at = Column(DateTime, default=datetime.utcnow)
    purpose = Column(String, nullable=False)
    # Populated once Nirali's logAccess() on-chain event is confirmed
    blockchain_tx_hash = Column(String, nullable=True)
