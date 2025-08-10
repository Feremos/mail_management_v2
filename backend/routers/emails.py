from app.dependencies import get_db
from app.schemas import EmailResponse
from app.dependencies import get_current_user  # albo z main.py
from app.crud import crud_get_emails_for_user, crud_get_email_detail

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from pathlib import Path

# Ścieżki: idź do katalogu nadrzędnego projektu
PROJECT_ROOT = Path(__file__).parent.parent.parent  # projekt/
TEMPLATES_DIR = PROJECT_ROOT / "frontend" / "templates"
STATIC_DIR = PROJECT_ROOT / "frontend" / "static"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(
    prefix='/emails',
    tags=['emails']
)

@router.get("/")
def get_emails_for_user(
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    inbox_id: int | None = None,
    category: str | None = None,
    mode: str = "json"
):
    emails = crud_get_emails_for_user(
        db,
        user_id=current_user.user_id,
        inbox_id=inbox_id,
        category=category
    )

    if mode == "html":
        return templates.TemplateResponse(
            "partials/emails_list.html",
            {"request": request, "emails": emails}
        )

    return emails



@router.get("/{email_id}")
def get_email_detail(
    email_id: int,
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    mode: str = "json"
):
    email = crud_get_email_detail(db, user_id=current_user.user_id, email_id=email_id)

    if mode == "html":
        return templates.TemplateResponse(
            "partials/email_detail.html",
            {"request": request, "email": email}
        )

    return email


