import imaplib
import email
from email.header import decode_header
from sqlalchemy.orm import Session
from app.models import Inbox, Email, UserSelectedInboxes, UserEmailCategory
from app.ai_agent import analyze_email_with_ai
from app.security import decrypt_password
from datetime import datetime


def fetch_emails_for_user(db: Session, user_id: int):
    """
    Pobiera maile tylko dla skrzynek wybranych przez konkretnego użytkownika.
    """
    # Pobierz wszystkie skrzynki wybrane przez użytkownika
    selected_inboxes = db.query(UserSelectedInboxes).filter(
        UserSelectedInboxes.user_id == user_id
    ).all()

    inbox_ids = [si.inbox_id for si in selected_inboxes]
    inboxes = db.query(Inbox).filter(Inbox.inbox_id.in_(inbox_ids)).all()

    for inbox in inboxes:
        try:
            fetch_and_save_emails_from_inbox(db, inbox, user_id)
        except Exception as e:
            print(f"Błąd przy pobieraniu maili z {inbox.login}: {e}")


def fetch_all_emails(db: Session):
    """
    Pobiera maile ze wszystkich skrzynek w systemie.
    """
    inboxes = db.query(Inbox).all()

    for inbox in inboxes:
        try:
            # Dla wszystkich maili nie przypisujemy do konkretnego użytkownika
            fetch_and_save_emails_from_inbox(db, inbox, None)
        except Exception as e:
            print(f"Błąd przy pobieraniu maili z {inbox.login}: {e}")


def fetch_and_save_emails_from_inbox(db: Session, inbox: Inbox, user_id: int = None):
    """
    Pobiera i zapisuje maile z konkretnej skrzynki.
    """
    # Tutaj powinno być prawdziwe deszyfrowanie hasła
    password = decrypt_password(inbox.password_encrypted)
    
    # Połączenie z serwerem IMAP
    mail = imaplib.IMAP4_SSL(inbox.imap_server, inbox.imap_port)
    mail.login(inbox.login, password)
    mail.select("inbox")

    # Pobierz wszystkie maile
    status, messages = mail.search(None, 'ALL')
    email_ids = messages[0].split()

    # Pobierz ostatnie 20 maili
    for e_id in email_ids[-20:]:
        res, msg = mail.fetch(e_id, "(RFC822)")
        for response_part in msg:
            if isinstance(response_part, tuple):
                msg_obj = email.message_from_bytes(response_part[1])
                save_email_to_db(db, inbox.inbox_id, msg_obj, user_id)

    mail.close()
    mail.logout()


def save_email_to_db(db: Session, inbox_id: int, msg, user_id: int = None):
    """
    Zapisuje pojedynczy email do bazy danych i analizuje go przez AI.
    Pomija maile z treścią HTML.
    """
    subject = decode_header(msg["Subject"])[0][0]
    if isinstance(subject, bytes):
        subject = subject.decode(errors="ignore")

    sent_from = msg.get("From")
    sent_to = msg.get("To")
    date_str = msg.get("Date")
    
    # Parsowanie daty
    try:
        date_received = datetime.strptime(date_str[:-6], "%a, %d %b %Y %H:%M:%S") if date_str else datetime.utcnow()
    except:
        date_received = datetime.utcnow()

    body = ""
    has_text_content = False
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            # Tylko tekstowe treści, bez załączników
            if "attachment" not in content_disposition and content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    try:
                        body += payload.decode(errors="ignore") + "\n"
                        has_text_content = True
                    except:
                        pass
    else:
        content_type = msg.get_content_type()
        # Tylko tekstowe treści
        if content_type == "text/plain":
            payload = msg.get_payload(decode=True)
            if payload:
                try:
                    body = payload.decode(errors="ignore")
                    has_text_content = True
                except:
                    body = str(payload)
                    has_text_content = True
        # Pomijaj całkowicie maile HTML i inne typy
        elif content_type == "text/html":
            return  # Pomijaj maile tylko z HTML
        else:
            return  # Pomijaj inne typy treści

    # Jeśli nie ma treści tekstowej, pomiń email
    if not has_text_content or not body.strip():
        return

    # Reszta funkcji bez zmian...
    # Sprawdź czy email już istnieje
    existing = db.query(Email).filter(
        Email.sent_from == sent_from, 
        Email.subject == subject,
        Email.inbox_id == inbox_id
    ).first()
    
    if not existing:
        # Jeśli użytkownik jest określony, analizuj przez AI
        if user_id:
            category, summary, suggested_reply = analyze_email_with_ai(db, user_id, subject, body)
        else:
            category, summary, suggested_reply = "Inne", "", ""
        
        new_email = Email(
            inbox_id=inbox_id,
            sent_from=sent_from,
            sent_to=sent_to,
            subject=subject,
            body=body,
            date_received=date_received,
            suggested_reply=suggested_reply
        )
        db.add(new_email)
        db.commit()
        db.refresh(new_email)
        
        # Jeśli użytkownik jest określony, zapisz kategorię
        if user_id:
            user_email_category = UserEmailCategory(
                user_id=user_id,
                email_id=new_email.email_id,
                category=category
            )
            db.add(user_email_category)
            db.commit()
            
    else:
        # Jeśli email już istnieje i mamy user_id, sprawdź czy mamy kategorię
        if user_id:
            existing_user_category = db.query(UserEmailCategory).filter(
                UserEmailCategory.user_id == user_id,
                UserEmailCategory.email_id == existing.email_id
            ).first()
            
            if not existing_user_category:
                # Analizuj przez AI i dodaj kategorię
                category, summary, suggested_reply = analyze_email_with_ai(db, user_id, subject, body)
                
                user_email_category = UserEmailCategory(
                    user_id=user_id,
                    email_id=existing.email_id,
                    category=category
                )
                db.add(user_email_category)
                db.commit()


