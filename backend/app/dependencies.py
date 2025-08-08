# dependencies.py - wersja z debugowaniem
from app.database import SessionLocal
from app.auth import verify_token
from app.models import User

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)):
    print("=" * 50)
    print("DEBUG get_current_user called")
    print("Request URL:", request.url)
    print("Request headers:", dict(request.headers))
    print("All cookies:", dict(request.cookies))
    
    token = request.cookies.get("access_token")
    print("Token from cookie:", repr(token))
    
    if not token:
        print("ERROR: No token found in cookies")
        raise HTTPException(status_code=401, detail="Not authenticated - no token")

    print("Calling verify_token...")
    username = verify_token(token)
    print("Username from token:", repr(username))
    
    if not username:
        print("ERROR: Token verification failed")
        raise HTTPException(status_code=401, detail="Invalid token")

    print("Querying database for user...")
    user = db.query(User).filter(User.username == username).first()
    print("User from database:", user)
    
    if not user:
        print("ERROR: User not found in database")
        raise HTTPException(status_code=401, detail="User not found")

    print("SUCCESS: User authenticated")
    print("=" * 50)
    return user