from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
from jose import jwt, JWTError
from fastapi import Request
from app.config import SECRET_KEY, ALGORITHM  # Twój config

class AuthRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Lista chronionych ścieżek
        protected_paths = ["/users/dashboard"]  # dodaj inne jeśli trzeba

        # Sprawdź czy URL jest chroniony
        if any(request.url.path.startswith(path) for path in protected_paths):
            token = request.cookies.get("access_token")  # lub z headera

            if not token:
                return RedirectResponse(url="/users/login")

            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                # Możesz tu sprawdzić dodatkowe rzeczy np. czy user istnieje w bazie
            except JWTError:
                return RedirectResponse(url="/users/login")

        # Przepuść dalej jeśli wszystko OK
        response = await call_next(request)
        return response