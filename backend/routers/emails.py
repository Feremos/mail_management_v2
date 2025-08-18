from app.dependencies import get_db
from app.schemas import EmailResponse
from app.dependencies import get_current_user
from app.crud import crud_get_emails_for_user, crud_get_email_detail, crud_update_email_category, crud_update_email_suggested_reply
from app.fetch_emails import fetch_emails_for_user  # Importujemy funkcję

from fastapi import APIRouter, Depends, Request, HTTPException
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

@router.post("/fetch")
def fetch_user_emails(
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    mode: str = "json"
):
    """
    Pobierz maile dla użytkownika i przeanalizuj je przez AI
    z użyciem kategorii wybranych przez użytkownika
    """
    try:
        # Pobierz maile i przeanalizuj je przez AI
        fetch_emails_for_user(db, current_user.user_id)
        
        if mode == "html":
            # Odśwież listę maili
            emails = crud_get_emails_for_user(db, current_user.user_id)
            return templates.TemplateResponse(
                "partials/emails_list.html",
                {"request": request, "emails": emails, "message": "Maile pobrane i przeanalizowane przez AI"}
            )
        
        return {"message": "Maile pobrane i przeanalizowane przez AI"}
    except Exception as e:
        if mode == "html":
            emails = crud_get_emails_for_user(db, current_user.user_id)
            return templates.TemplateResponse(
                "partials/emails_list.html",
                {"request": request, "emails": emails, "error": f"Błąd: {str(e)}"}
            )
        raise HTTPException(status_code=500, detail=f"Błąd podczas pobierania maili: {str(e)}")

@router.put("/{email_id}/category")
def update_email_category(
    email_id: int,
    category: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Aktualizuj kategorię emaila"""
    return crud_update_email_category(db, current_user.user_id, email_id, category)

@router.put("/{email_id}/suggested-reply")
def update_suggested_reply(
    email_id: int,
    suggested_reply: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Aktualizuj sugerowaną odpowiedź"""
    return crud_update_email_suggested_reply(db, email_id, suggested_reply)

@router.post("/{email_id}/analyze")
def analyze_email_with_ai(
    email_id: int,
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    mode: str = "json"
):
    """
    Ponowna analiza pojedynczego maila przez AI
    """
    try:
        # Pobierz email
        email = crud_get_email_detail(db, current_user.user_id, email_id)
        
        # Zaimportuj AI agenta
        from app.ai_agent import analyze_email_with_ai as ai_analyze
        
        # Analizuj przez AI
        category, summary, suggested_reply = ai_analyze(
            db, current_user.user_id, email.subject, email.body
        )
        
        # Zaktualizuj dane
        crud_update_email_category(db, current_user.user_id, email_id, category)
        crud_update_email_suggested_reply(db, email_id, suggested_reply)
        
        # Odśwież email
        updated_email = crud_get_email_detail(db, current_user.user_id, email_id)
        
        if mode == "html":
            return templates.TemplateResponse(
                "partials/email_detail.html",
                {"request": request, "email": updated_email}
            )
        
        return {
            "message": "Email przeanalizowany przez AI",
            "category": category,
            "summary": summary,
            "suggested_reply": suggested_reply
        }
        
    except Exception as e:
        if mode == "html":
            email = crud_get_email_detail(db, current_user.user_id, email_id)
            return templates.TemplateResponse(
                "partials/email_detail.html",
                {"request": request, "email": email, "error": f"Błąd AI: {str(e)}"}
            )
        raise HTTPException(status_code=500, detail=f"Błąd AI: {str(e)}")
    
@router.post("/reanalyze")
def reanalyze_user_emails(
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    mode: str = "json"
):
    """
    Ponownie analizuje wszystkie maile użytkownika przez AI
    z użyciem aktualnych kategorii
    """
    try:
        # Pobierz wszystkie maile użytkownika
        emails = crud_get_emails_for_user(db, current_user.user_id)
        
        # Liczniki dla postępu
        processed = 0
        total = len(emails)
        
        print(f"🚀 Rozpoczynam reanalizę {total} maili...")
        
        # Dla każdego maila - ponowna analiza przez AI
        for email in emails:
            try:
                from app.ai_agent import analyze_email_with_ai
                
                # Analizuj przez AI z aktualnymi kategoriami
                category, summary, suggested_reply = analyze_email_with_ai(
                    db, current_user.user_id, email.subject, email.body
                )
                
                # Zaktualizuj kategorię
                crud_update_email_category(db, current_user.user_id, email.email_id, category)
                
                # Zaktualizuj sugerowaną odpowiedź
                crud_update_email_suggested_reply(db, email.email_id, suggested_reply)
                
                processed += 1
                print(f"✅ Przeanalizowano {processed}/{total}: {email.subject[:50]}...")
                
            except Exception as e:
                print(f"❌ Błąd przy reanalizie maila {email.email_id} ({email.subject[:30]}): {e}")
                continue
        
        success_message = f"Przeanalizowano {processed} z {total} maili przez AI"
        print(f"✅ {success_message}")
        
        if mode == "html":
            # Odśwież listę maili
            updated_emails = crud_get_emails_for_user(db, current_user.user_id)
            return templates.TemplateResponse(
                "partials/emails_list.html",
                {
                    "request": request, 
                    "emails": updated_emails, 
                    "message": success_message
                }
            )
        
        return {"message": success_message}
        
    except Exception as e:
        error_msg = f"Błąd podczas reanalizy maili: {str(e)}"
        print(f"❌ {error_msg}")
        
        if mode == "html":
            emails = crud_get_emails_for_user(db, current_user.user_id)
            return templates.TemplateResponse(
                "partials/emails_list.html",
                {"request": request, "emails": emails, "error": error_msg}
            )
        raise HTTPException(status_code=500, detail=error_msg)