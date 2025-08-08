# dependencies.py - wersja z debugowaniem
from app.database import SessionLocal
from app.auth import verify_token
from app.models import User, RevokedToken

from starlette.responses import RedirectResponse
from urllib.parse import urlencode
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/users/login", status_code=303)

    revoked = db.query(RevokedToken).filter(RevokedToken.token == token).first()
    if revoked:
        return RedirectResponse(url="/users/login", status_code=303)

    username = verify_token(token)
    if not username:
        return RedirectResponse(url="/users/login", status_code=303)

    user = db.query(User).filter(User.username == username).first()
    if not user:
        return RedirectResponse(url="/users/login", status_code=303)

    return user
