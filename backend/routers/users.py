# users.py
from app.security import create_access_token, verify_password, get_token_exp
from app.dependencies import get_current_user, get_db  # Importuj z dependencies
from app.schemas import UserCreate, UserResponse, UserLogin, Token
from app.models import User
from app.crud import crud_create_user, crud_add_revoked_token, crud_get_emails_for_user

from fastapi import APIRouter, Depends, HTTPException, Request, Form, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

router = APIRouter(
    prefix="/users",
    tags=['users']
)

ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Ścieżki: idź do katalogu nadrzędnego projektu
PROJECT_ROOT = Path(__file__).parent.parent.parent  # projekt/
TEMPLATES_DIR = PROJECT_ROOT / "frontend" / "templates"
STATIC_DIR = PROJECT_ROOT / "frontend" / "static"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Post creating user in Users
@router.post("/create", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = crud_create_user(db, user=user)  # Przekazuj cały obiekt
    if not db_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    return db_user

@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# Post login endpoint with JWT access token
@router.post("/login")
def login_user(
    request: Request,  # Dodaj Request
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    print("=== LOGIN DEBUG ===")
    print(f"Login attempt for user: {username}")
    
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user or not verify_password(password, db_user.password_hashed):
        print("Invalid credentials")
        # Lepiej zwrócić template z błędem zamiast JSON
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Invalid username or password"
        })

    # Tworzymy token
    
    access_token = create_access_token(username=str(db_user.username))
    print(f"Generated token: {access_token}")

    # Tworzymy response z przekierowaniem
    response = RedirectResponse(url="/users/dashboard", status_code=303)
    
    # Zapisujemy token w ciasteczku
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=1800,  # 30 minut
        path="/",
        samesite="lax",
        secure=False  # Dla localhost - zmień na True na produkcji z HTTPS
    )
    
    print("Cookie set in response")
    return response

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
    
@router.get("/me", response_model=UserResponse)
def read_user_me(current_user: User = Depends(get_current_user)): # get current user
    return current_user


@router.get("/dashboard")
async def dashboard(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user is not None:
        emails = crud_get_emails_for_user(db, user_id=current_user.user_id)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "current_user": current_user,
            "emails": emails,
        }
    )

# Endpoint do wylogowania
@router.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if token:
        exp = get_token_exp(token)
        if exp:
            crud_add_revoked_token(db, token, exp)

    response = RedirectResponse(url="/users/login", status_code=303)
    response.delete_cookie("access_token", path="/")
    return response