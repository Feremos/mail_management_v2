from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://emails_db_j93c_user:oZWEJflM5igHH1sEJiICTZBWerv7hb4Z@dpg-d1v1fmruibrs738v0u30-a.frankfurt-postgres.render.com/mail_manager_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()