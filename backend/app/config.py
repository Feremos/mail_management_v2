from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
FERNET_KEY = os.getenv("FERNET_KEY").strip()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

print(f"Loaded SECRET_KEY: {repr(SECRET_KEY)}")
