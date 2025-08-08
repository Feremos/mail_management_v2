from app.schemas import UserResponse, SelectInboxRequest, InboxSelectionResponse
from app.models import User, Inbox, UserSelectedInboxes
from app.dependencies import get_db, get_current_user

from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/inboxes",
    tags=['inboxes']
)

#Post select an inbox to add to user_selected_inboxes
@router.post("/select", response_model=InboxSelectionResponse)
def select_inbox(
    login: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Sprawdź, czy inbox istnieje
    inbox = db.query(Inbox).filter(Inbox.login == login).first()

    if not inbox:
        # Jeśli nie ma inboxa, zwróć błąd
        raise HTTPException(status_code=404, detail="Inbox o podanym loginie nie istnieje")

    # (opcjonalnie) Tu możesz dodać weryfikację hasła — np. spróbować się połączyć, jeśli chcesz

    # Sprawdź, czy użytkownik już wybrał ten inbox
    existing_selection = db.query(UserSelectedInboxes).filter(
        UserSelectedInboxes.user_id == current_user.user_id,
        UserSelectedInboxes.inbox_id == inbox.inbox_id
    ).first()

    if existing_selection:
        raise HTTPException(status_code=400, detail="Już masz tę skrzynkę wybraną")

    # Dodaj inbox do usera
    ########### to add crud
    selected_inbox = UserSelectedInboxes(user_id=current_user.user_id, inbox_id=inbox.inbox_id)
    db.add(selected_inbox)
    db.commit()
    db.refresh(selected_inbox)

    return InboxSelectionResponse(
        inbox_id=inbox.inbox_id,
        name=inbox.login,  # lub inna nazwa jeśli masz
        login=inbox.login
    )

#Get user selected inboxes
@router.get("/selected", response_model=list[InboxSelectionResponse])
def get_selected_inboxes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = (
        db.query(Inbox)
        .join(UserSelectedInboxes, Inbox.inbox_id == UserSelectedInboxes.inbox_id)
        .filter(UserSelectedInboxes.user_id == current_user.user_id)
        .all()
    )
    return result