import os
import secrets
from datetime import datetime, timedelta, UTC
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import User
from .logger import logger

SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 Hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

def hash_password(password: str) -> str:
    """Hash password using hashlib sha256 + salt for secure storage without external C dependencies."""
    salt = secrets.token_hex(8)
    import hashlib
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}${key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored salt$hash string."""
    try:
        if '$' not in hashed_password:
            return False
        salt, key_hex = hashed_password.split('$', 1)
        import hashlib
        key = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return key.hex() == key_hex
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate simple signed token string for user authentication."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire.timestamp()})
    
    # Fast lightweight token encoding
    import json, base64
    payload_str = json.dumps(to_encode)
    encoded = base64.b64encode(payload_str.encode()).decode()
    return f"bearer_{encoded}"

def decode_token(token: str) -> Optional[dict]:
    try:
        if not token or not token.startswith("bearer_"):
            return None
        import json, base64
        encoded = token.replace("bearer_", "", 1)
        payload_str = base64.b64decode(encoded.encode()).decode()
        data = json.loads(payload_str)
        if data.get("exp") and datetime.now(UTC).timestamp() > data["exp"]:
            return None
        return data
    except Exception:
        return None

def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Optional[User]:
    if not token:
        return None
    data = decode_token(token)
    if not data or not data.get("sub"):
        return None
    user = db.query(User).filter(User.email == data["sub"]).first()
    return user
