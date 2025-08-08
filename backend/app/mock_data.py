from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import User, Inbox, Email
import hashlib
from datetime import datetime

def get_password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_mock_data():
    db = SessionLocal()
    
    # Sprawdź czy użytkownik już istnieje
    user = db.query(User).filter(User.username == "jan").first()
    if not user:
        user = User(
            username="jan",
            password_hashed=get_password_hash("12345")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Sprawdź czy są skrzynki
    inboxes = db.query(Inbox).all()
    if not inboxes:
        inbox1 = Inbox(
            user_id=user.user_id,
            login="jan@gmail.com",
            password_encrypted="encrypted_pass_1",
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            imap_server="imap.gmail.com",
            imap_port=993
        )
        
        inbox2 = Inbox(
            user_id=user.user_id,
            login="anna@wp.pl",
            password_encrypted="encrypted_pass_2",
            smtp_server="smtp.wp.pl",
            smtp_port=587,
            imap_server="imap.wp.pl",
            imap_port=993
        )
        
        db.add(inbox1)
        db.add(inbox2)
        db.commit()
        db.refresh(inbox1)
        db.refresh(inbox2)
    else:
        inbox1 = inboxes[0]
    
    # Dodaj mockowe emaile
    email1 = Email(
        inbox_id=inbox1.inbox_id,
        sent_from="boss@company.com",
        sent_to="jan@gmail.com",
        subject="Ważne: Spotkanie jutro",
        body="Cześć Jan, przypominam o spotkaniu jutro o 10:00. Pozdrawiam, Szef",
        suggested_reply="Oczywiście, będę na spotkaniu.",
        date_received=datetime(2024, 1, 15, 9, 30)
    )
    
    email2 = Email(
        inbox_id=inbox1.inbox_id,
        sent_from="newsletter@shop.com",
        sent_to="jan@gmail.com",
        subject="Nowe promocje!",
        body="Sprawdź nasze nowe promocje. Rabat 50% na wszystko!",
        date_received=datetime(2024, 1, 14, 14, 15)
    )
    
    db.add(email1)
    db.add(email2)
    db.commit()
    
    print("Mock data created!")

if __name__ == "__main__":
    create_mock_data()