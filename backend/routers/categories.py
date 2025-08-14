from fastapi import APIRouter, Depends, HTTPException, Request, Form
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models import Category, UserSelectedCategories
from app.schemas import CategoryCreate
from app.crud import crud_add_or_get_category, crud_add_user_category, crud_get_user_categories, crud_get_user_selected_categories, crud_remove_user_category
from fastapi.templating import Jinja2Templates
from pathlib import Path

# Ścieżki: idź do katalogu nadrzędnego projektu
PROJECT_ROOT = Path(__file__).parent.parent.parent  # projekt/
TEMPLATES_DIR = PROJECT_ROOT / "frontend" / "templates"
STATIC_DIR = PROJECT_ROOT / "frontend" / "static"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))



router = APIRouter(prefix="/categories", tags=["categories"])

# Tutaj endpointy do kategorii (te które wyżej podałem)
@router.get("/")
def get_user_categories(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    mode: str = "json"
):
    categories = crud_get_user_selected_categories(db, current_user.user_id)


    if mode == "html":
        return templates.TemplateResponse(
            "partials/categories_list.html",
            {"request": request, "categories": categories}
        )

    return categories


@router.post("/add_user_category")
def add_user_category(
    request: Request,
    category_name: str = Form(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # logika dodania (unikalność + przypisanie userowi)
    category = crud_add_or_get_category(db, category_name.strip())
    crud_add_user_category(db, current_user.user_id, category.id)

    categories = crud_get_user_categories(db, current_user.user_id)
    return templates.TemplateResponse(
        "partials/categories_list.html",
        {"request": request, "categories": categories}
    )



@router.delete("/{category_id}")
def remove_user_category(
    request: Request,
    category_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    crud_remove_user_category(db, current_user.user_id, category_id)
    categories = crud_get_user_categories(db,current_user.user_id)

    return templates.TemplateResponse(
        "partials/categories_list.html",
        {"request": request, "categories": categories}
    )