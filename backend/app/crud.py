from app.schemas import UserCreate,SelectInboxRequest
from app.models import User, Inbox, UserSelectedInboxes, Email, RevokedToken, UserSelectedCategories, Category, UserEmailCategory
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

def crud_get_emails_for_user(
    db: Session,
    user_id: int,
    inbox_id: int | None = None,
    category: str | None = None 
):
    """
    Zwraca listę emaili użytkownika z kategorią z tabeli UserEmailCategory.
    Nadpisuje classification w obiekcie Email, żeby frontend działał bez zmian.
    """
    selected_inbox_ids = [
        selection.inbox_id
        for selection in db.query(UserSelectedInboxes)
        .filter(UserSelectedInboxes.user_id == user_id)
        .all()
    ]
    if not selected_inbox_ids:
        return []

    query = (
        db.query(Email, UserEmailCategory.category.label("user_category"))
        .join(UserEmailCategory, Email.email_id == UserEmailCategory.email_id)
        .filter(Email.inbox_id.in_(selected_inbox_ids))
        .filter(UserEmailCategory.user_id == user_id)
    )

    if inbox_id and inbox_id in selected_inbox_ids:
        query = query.filter(Email.inbox_id == inbox_id)

    if category:
        query = query.filter(UserEmailCategory.category == category)

    results = query.order_by(Email.date_received.desc()).all()

    # Nadpisanie classification dla frontendu
    emails = []
    for email_obj, user_category in results:
        email_obj.classification = user_category
        emails.append(email_obj)

    return emails


def crud_get_email_detail(db: Session, user_id: int, email_id: int):
    """
    Zwraca szczegóły emaila z kategorią z UserEmailCategory.
    Nadpisuje classification w obiekcie Email.
    """
    result = (
        db.query(Email, UserEmailCategory.category.label("user_category"))
        .join(UserSelectedInboxes, Email.inbox_id == UserSelectedInboxes.inbox_id)
        .join(UserEmailCategory, Email.email_id == UserEmailCategory.email_id)
        .filter(
            UserSelectedInboxes.user_id == user_id,
            UserEmailCategory.user_id == user_id,
            Email.email_id == email_id
        )
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="Email not found or not accessible")

    email_obj, user_category = result
    email_obj.classification = user_category
    return email_obj




def crud_add_revoked_token(db: Session, token: str, expires_at):
    """
    Dodaje token do listy zablokowanych (revoked_tokens).
    """
    revoked = RevokedToken(token=token, expires_at=expires_at)
    db.add(revoked)
    db.commit()
    db.refresh(revoked)
    return revoked

def crud_add_or_get_category(db: Session, name: str):
    category = db.query(Category).filter(Category.name == name).first()
    if not category:
        category = Category(name=name)
        db.add(category)
        db.commit()
        db.refresh(category)
    return category

def crud_add_user_category(db: Session, user_id: int, category_id: int):
    exists = db.query(UserSelectedCategories).filter(
        UserSelectedCategories.user_id == user_id,
        UserSelectedCategories.category_id == category_id,
    ).first()
    if not exists:
        user_cat = UserSelectedCategories(user_id=user_id, category_id=category_id)
        db.add(user_cat)
        db.commit()

def crud_get_user_categories(db: Session, user_id: int):
    return (
        db.query(Category)
        .join(UserSelectedCategories, Category.id == UserSelectedCategories.category_id)
        .filter(UserSelectedCategories.user_id == user_id)
        .order_by(Category.name)
        .all()
    )
    
def crud_get_user_selected_categories(db, user_id):
    return (
        db.query(Category)
        .join(UserSelectedCategories, UserSelectedCategories.category_id == Category.id)
        .filter(UserSelectedCategories.user_id == user_id)
        .all()
    )

def crud_remove_user_category(db, user_id, category_id):
    user_cat = db.query(UserSelectedCategories).filter(
        UserSelectedCategories.user_id == user_id,
        UserSelectedCategories.category_id == category_id
    ).first()

    if not user_cat:
        raise HTTPException(status_code=404, detail="Kategoria nie przypisana do użytkownika")

    db.delete(user_cat)
    db.commit()
    
def crud_add_user_inbox(db, user_id, login):
    inbox = db.query(Inbox).filter(Inbox.login == login).first()
    if not inbox:
        raise HTTPException(status_code=404, detail="Inbox o podanym loginie nie istnieje")

    existing_selection = db.query(UserSelectedInboxes).filter(
        UserSelectedInboxes.user_id == user_id,
        UserSelectedInboxes.inbox_id == inbox.inbox_id
    ).first()

    if existing_selection:
        raise HTTPException(status_code=400, detail="Już masz tę skrzynkę wybraną")

    selected_inbox = UserSelectedInboxes(user_id=user_id, inbox_id=inbox.inbox_id)
    db.add(selected_inbox)
    db.commit()
    db.refresh(selected_inbox)

    return inbox


def crud_get_user_inboxes(db, user_id):
    return (
        db.query(Inbox)
        .join(UserSelectedInboxes, Inbox.inbox_id == UserSelectedInboxes.inbox_id)
        .filter(UserSelectedInboxes.user_id == user_id)
        .all()
    )
    
def crud_update_email_suggested_reply(db: Session, email_id: int, suggested_reply: str):
    """
    Aktualizuje sugerowaną odpowiedź dla emaila.
    """
    email = db.query(Email).filter(Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    email.suggested_reply = suggested_reply
    db.commit()
    db.refresh(email)
    return email

def crud_update_email_category(db: Session, user_id: int, email_id: int, category: str):
    """
    Aktualizuje kategorię emaila dla użytkownika.
    """
    # Najpierw sprawdź czy email istnieje i czy użytkownik ma do niego dostęp
    email = db.query(Email).filter(Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Sprawdź czy użytkownik ma dostęp do skrzynki tego emaila
    user_has_access = db.query(UserSelectedInboxes).filter(
        UserSelectedInboxes.user_id == user_id,
        UserSelectedInboxes.inbox_id == email.inbox_id
    ).first()
    
    if not user_has_access:
        raise HTTPException(status_code=403, detail="Brak dostępu do tego emaila")
    
    # Znajdź lub utwórz kategorię użytkownika dla tego emaila
    user_email_category = db.query(UserEmailCategory).filter(
        UserEmailCategory.user_id == user_id,
        UserEmailCategory.email_id == email_id
    ).first()
    
    if user_email_category:
        user_email_category.category = category
    else:
        user_email_category = UserEmailCategory(
            user_id=user_id,
            email_id=email_id,
            category=category
        )
        db.add(user_email_category)
    
    db.commit()
    db.refresh(user_email_category)
    return user_email_category