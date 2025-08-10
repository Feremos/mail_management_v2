from app.schemas import UserResponse, SelectInboxRequest, InboxSelectionResponse
from app.models import User, Inbox, UserSelectedInboxes
from app.dependencies import get_db, get_current_user
from app.crud import crud_add_user_inbox, crud_get_user_inboxes
from fastapi import APIRouter, Depends, HTTPException, Form, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from pathlib import Path

# Ścieżki: idź do katalogu nadrzędnego projektu
PROJECT_ROOT = Path(__file__).parent.parent.parent  # projekt/
TEMPLATES_DIR = PROJECT_ROOT / "frontend" / "templates"
STATIC_DIR = PROJECT_ROOT / "frontend" / "static"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(
    prefix="/inboxes",
    tags=['inboxes']
)

#tutaj jest cos zle zrobione trzeba poprawic
@router.post("/select")
def select_inbox(
    request: Request,
    login: str = Form(...),
    password: str = Form(...),  # aktualnie nieużywane, trzeba dodac weryfikacje potem
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    mode: str = "json"
):
    inbox = crud_add_user_inbox(db, current_user.user_id, login)

    if mode == "html":
        inboxes = crud_get_user_inboxes(db, current_user.user_id)
        return templates.TemplateResponse(
            "partials/inboxes_list.html",
            {"request": request, "inboxes": inboxes}
        )
    
    return InboxSelectionResponse(
        inbox_id=inbox.inbox_id,
        name=inbox.login,
        login=inbox.login
    )


#Get user selected inboxes
@router.get("/selected")
def get_selected_inboxes(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    mode: str = "json"
):
    inboxes = (
        db.query(Inbox)
        .join(UserSelectedInboxes, Inbox.inbox_id == UserSelectedInboxes.inbox_id)
        .filter(UserSelectedInboxes.user_id == current_user.user_id)
        .all()
    )

    if mode == "html":
        return templates.TemplateResponse(
            "partials/inboxes_list.html",
            {"request": request, "inboxes": inboxes}
        )

    return inboxes  # JSON domyślnie

@router.delete("/{inbox_id}/unselect")
def unselect_inbox(
    inbox_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Usuń skrzynkę z listy wybranych przez użytkownika"""
    
    user_inbox = db.query(UserSelectedInboxes).filter(
        UserSelectedInboxes.user_id == current_user.user_id,
        UserSelectedInboxes.inbox_id == inbox_id
    ).first()

    if not user_inbox:
        raise HTTPException(status_code=404, detail="Skrzynka nie przypisana do użytkownika")

    db.delete(user_inbox)
    db.commit()

    return {"msg": "Skrzynka usunięta z listy"}