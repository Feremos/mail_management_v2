import os
from typing import List, Tuple
from app.models import Category
from sqlalchemy.orm import Session
from openai import OpenAI  # Nowe API

# Inicjalizacja klienta OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_user_categories(db: Session, user_id: int) -> List[str]:
    """Pobiera kategorie wybrane przez użytkownika"""
    categories = db.query(Category).join(
        Category.user_associations
    ).filter(
        Category.user_associations.any(user_id=user_id)
    ).all()
    
    return [cat.name for cat in categories]

def analyze_email_with_ai(
    db: Session, 
    user_id: int, 
    subject: str, 
    body: str
) -> Tuple[str, str, str]:
    """
    Analizuje email za pomocą AI i zwraca:
    (kategoria, streszczenie, sugerowana_odpowiedz)
    """
    
    # Pobierz kategorie użytkownika
    user_categories = get_user_categories(db, user_id)
    
    # Prompt dla AI
    prompt = f"""
    Przeanalizuj następujący email i odpowiedz w formacie JSON:

    Temat: {subject}
    Treść: {body}

    Dostępne kategorie: {', '.join(user_categories) if user_categories else 'Brak kategorii'}

    Odpowiedz w formacie JSON z polami:
    - "category": najbardziej pasująca kategoria (wybierz z dostępnych lub "Inne")
    - "summary": krótkie streszczenie emaila (max 100 słów)
    - "suggested_reply": profesjonalna sugerowana odpowiedź (max 200 słów)

    Przykład odpowiedzi:
    {{
        "category": "Oferta handlowa",
        "summary": "Klient pyta o cenę produktu X",
        "suggested_reply": "Dziękujemy za zainteresowanie..."
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Jesteś asystentem analizującym emaile. Odpowiadaj tylko w formacie JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        # Parsowanie odpowiedzi
        ai_response = response.choices[0].message.content.strip()
        
        # Prosta walidacja JSON
        import json
        try:
            result = json.loads(ai_response)
            category = result.get("category", "Inne")
            summary = result.get("summary", "")
            suggested_reply = result.get("suggested_reply", "")
            
            return category, summary, suggested_reply
        except json.JSONDecodeError:
            # Jeśli AI nie zwróciło poprawnego JSON, użyj domyślnych wartości
            return "Inne", "Nie udało się wygenerować streszczenia", "Nie udało się wygenerować odpowiedzi"
            
    except Exception as e:
        print(f"❌ Błąd AI: {e}")
        return "Inne", "Błąd analizy", "Błąd generowania odpowiedzi"