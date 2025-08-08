from app.schemas import UserCreate,SelectInboxRequest
from app.models import User, Inbox, UserSelectedInboxes, Email, RevokedToken
from app.dependencies import Session, get_db
from app.security import get_password_hash, get_current_user_api

from fastapi import Depends, HTTPException
from sqlalchemy import desc


def crud_create_user(db: Session, user: UserCreate):
    # Sprawdź czy użytkownik istnieje
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        return None
    
    # Utwórz nowego użytkownika z zahashowanym hasłem
    password_hashed = get_password_hash(user.password)  # Funkcja do hashowania
    db_user = User(
        username=user.username,
        password_hashed=password_hashed  # Używamy poprawnej nazwy kolumny
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
def crud_select_inbox_for_user(
    request: SelectInboxRequest,
    current_user = Depends(get_current_user_api),
    db: Session = Depends(get_db)
):
    inbox = db.query(Inbox).filter(Inbox.inbox_id == request.inbox_id).first()
    if not inbox:
        raise HTTPException(status_code=404, detail="Inbox not found")

    existing = db.query(UserSelectedInboxes).filter(
        UserSelectedInboxes.user_id == current_user.user_id,
        UserSelectedInboxes.inbox_id == request.inbox_id
    ).first()
    if existing:
        return False

    selected = UserSelectedInboxes(user_id=current_user.user_id, inbox_id=request.inbox_id)
    db.add(selected)
    db.commit()

    return True

def crud_get_emails_for_user(db: Session, user_id: int):
    selected_inbox_ids=[
        selection.inbox_id
        for selection in db.query(UserSelectedInboxes).filter(
            UserSelectedInboxes.user_id == user_id
        ).all()
    ]
    
    if not selected_inbox_ids:
        return []
        
    
    return (
        db.query(Email).filter(Email.inbox_id.in_(selected_inbox_ids)).order_by(Email.date_received.desc()).all()
    )


def crud_add_revoked_token(db: Session, token: str, expires_at):
    """
    Dodaje token do listy zablokowanych (revoked_tokens).
    """
    revoked = RevokedToken(token=token, expires_at=expires_at)
    db.add(revoked)
    db.commit()
    db.refresh(revoked)
    return revoked