# app/auth_utils.py
from jose import JWTError, jwt
from app.config import SECRET_KEY, ALGORITHM

def verify_token(token: str) -> str | None:
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        return username
    except JWTError as e:
        return None