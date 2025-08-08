# security.py
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models import User
from app.auth import verify_token
import os
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from app.config import SECRET_KEY, ALGORITHM
from datetime import datetime, timezone

ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Konfiguracja hashowania haseł
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash verification
def get_password_hash(password):
    return pwd_context.hash(password)

# Password verification
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# JWT token generation
def create_access_token(username: str, expires_delta: timedelta = None):
    to_encode = {"sub": username}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    

    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

# OAuth2 scheme dla API endpoints (jeśli potrzebne)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

# Dependency for API endpoints using Authorization header
def get_current_user_api(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)): # its in crud
    username = verify_token(token)
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

def get_token_exp(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_timestamp = payload.get("exp")
        if exp_timestamp is None:
            return None
        return datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
    except jwt.ExpiredSignatureError:
        # Token już wygasł
        return datetime.now(tz=timezone.utc)
    except jwt.PyJWTError:
        # Niepoprawny token
        return None