from app.schemas import UserResponse, SelectInboxRequest, InboxSelectionResponse
from app.models import User, Inbox, UserSelectedInboxes
from app.dependencies import get_db, get_current_user

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/inboxes",
    tags=['inboxes']
)

#Post select an inbox to add to user_selected_inboxes
@router.post("/select", response_model=UserResponse, ) 
def select_inbox(request: SelectInboxRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    inbox = db.query(Inbox).filter(Inbox.inbox_id == request.inbox_id).first()
    if not inbox:
        raise HTTPException(status_code=404, detail="Inbox not found")
    
    #Did user already select this inbox
    existing = db.query(UserSelectedInboxes).filter(Inbox.inbox_id == request.inbox_id, UserSelectedInboxes.user_id == current_user.user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already selected this inbox")
    
    #Create new selection
    selected_inbox = UserSelectedInboxes(user_id=current_user.user_id, inbox_id=request.inbox_id)
    db.add(selected_inbox)
    db.commit()
    

    return {"message": "Inbox selected succesfully", "selected_inbox_id": selected_inbox.id}

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