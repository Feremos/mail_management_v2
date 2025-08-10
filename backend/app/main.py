from fastapi import FastAPI 
from fastapi.responses import RedirectResponse
from app.database import engine, Base
from routers import users,inboxes,emails, admin, categories

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from routers.middleware import AuthRedirectMiddleware
from pathlib import Path

# Ścieżki: idź do katalogu nadrzędnego projektu
PROJECT_ROOT = Path(__file__).parent.parent.parent  # projekt/
TEMPLATES_DIR = PROJECT_ROOT / "frontend" / "templates"
STATIC_DIR = PROJECT_ROOT / "frontend" / "static"




Base.metadata.create_all(bind=engine)

app = FastAPI()

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tymczasowo dla testów
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name='static')

app.add_middleware(AuthRedirectMiddleware)
app.include_router(users.router)
app.include_router(inboxes.router)
app.include_router(emails.router)
app.include_router(admin.router)
app.include_router(categories.router)

@app.get("/")
def root():
    """Przekierowanie głównej strony na logowanie"""
    return RedirectResponse(url="/users/login", status_code=302)


