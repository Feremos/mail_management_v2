from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.models import Inbox, User
from app.dependencies import get_current_user, get_db
from app.security import encrypt_password
from fastapi.templating import Jinja2Templates
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent  # projekt/
TEMPLATES_DIR = PROJECT_ROOT / "frontend" / "templates"
STATIC_DIR = PROJECT_ROOT / "frontend" / "static"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIR)

@router.get("/admin_panel")
async def add_inbox_form(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("admin_panel.html", {"request": request, "current_user": current_user})

@router.post("/inboxes/add")
async def add_inbox(
    request: Request,
    login: str = Form(...),
    password: str = Form(...),
    smtp_server: str = Form(...),
    smtp_port: int = Form(...),
    imap_server: str = Form(...),
    imap_port: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    encrypted_password = encrypt_password(password)

    new_inbox = Inbox(
        login=login,
        password_encrypted=encrypted_password,
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        imap_server=imap_server,
        imap_port=imap_port,
    )
    db.add(new_inbox)
    db.commit()
    db.refresh(new_inbox)

    return RedirectResponse(url="/admin_panel", status_code=303)
