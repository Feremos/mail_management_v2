from pydantic import BaseModel, Field
#from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    
class TokenData(BaseModel):
    username:str
    
class InboxCreate(BaseModel):
    login: str
    password: str  # plain text, potem zaszyfrujemy
    smtp_server: str
    smtp_port: int
    imap_server: str
    imap_port: int
    
class UserResponse(BaseModel):
    user_id: int
    username: str
    
class InboxResponse(BaseModel):
    inbox_id: int
    login: str
    smtp_server: str
    smtp_port: int
    imap_server: str
    imap_port: int

class EmailResponse(BaseModel):
    email_id: int
    sent_from: str
    sent_to: str
    subject: str
    body: str
    date_received: datetime
    responded: bool
    archived: bool
    
    class Config:
        from_attributes = True
    
class SelectInboxRequest(BaseModel):
    inbox_id: int
    
class InboxSelectionResponse(BaseModel):
    """
    Schemat danych używany do zwracania informacji o skrzynce e-mail, 
    którą użytkownik może wybrać lub ma już wybraną w aplikacji.

    Ten model określa, jakie dane są widoczne dla użytkownika (frontendu) 
    podczas wybierania lub przeglądania swoich skrzynek.

    Pola:
        inbox_id (int) - unikalny identyfikator skrzynki
        name (str)     - przyjazna nazwa, np. "Wsparcie", "Sprzedaż"
        login (str)    - adres e-mail skrzynki, np. "support@firm.pl" (do wyświetlenia)
    """
    inbox_id: int
    name: str  # np. "Wsparcie", "Sprzedaż"
    login: str  # opcjonalnie: jeśli chcesz pokazać "support@firm.pl", ale nie koniecznie

    class Config:
        from_attributes = True