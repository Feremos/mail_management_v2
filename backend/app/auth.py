# app/auth_utils.py
from jose import JWTError, jwt
from app.config import SECRET_KEY, ALGORITHM

def verify_token(token: str) -> str | None:
    print("=== VERIFY TOKEN DEBUG ===")
    print("SECRET_KEY in verify_token:", repr(SECRET_KEY))
    print("Token to verify:", repr(token))
    print("Algorithm:", ALGORITHM)
    
    if not SECRET_KEY:
        print("ERROR: SECRET_KEY is empty!")
        return None
    
    if not token:
        print("ERROR: Token is empty!")
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("Decoded payload:", payload)
        username = payload.get("sub")
        print("Username from payload:", repr(username))
        return username
    except JWTError as e:
        print("JWTError:", str(e))
        print("JWTError type:", type(e))
        return None