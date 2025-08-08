from app.dependencies import get_db
from app.schemas import EmailResponse
from app.dependencies import get_current_user  # albo z main.py
from app.crud import crud_get_emails_for_user

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(
    prefix='/emails',
    tags=['emails']
)

@router.get("/", response_model = list[EmailResponse])
def get_emails_for_user(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Return all emails for user
    """
    emails = crud_get_emails_for_user(db, user_id=current_user.user_id)
    
    return emails




