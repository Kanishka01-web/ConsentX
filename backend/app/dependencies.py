from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from . import models
from .database import get_db
from .services.auth_service import decode_access_token

security_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")

    return user


def require_data_principal(user: models.User = Depends(get_current_user)) -> models.User:
    if user.role != models.UserRole.DATA_PRINCIPAL:
        raise HTTPException(status_code=403, detail="This action requires a data_principal account")
    return user


def require_data_fiduciary(user: models.User = Depends(get_current_user)) -> models.User:
    if user.role != models.UserRole.DATA_FIDUCIARY:
        raise HTTPException(status_code=403, detail="This action requires a data_fiduciary account")
    return user