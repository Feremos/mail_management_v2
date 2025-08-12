from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hashed = Column(String)
    
    selected_inboxes = relationship("UserSelectedInboxes", back_populates="user", cascade="all, delete-orphan")
    selected_categories = relationship("UserSelectedCategories", back_populates="user", cascade="all, delete-orphan")
    

class Inbox(Base):
    __tablename__ = "inboxes"
    
    inbox_id = Column(Integer, primary_key=True, index=True)
    login = Column(String)
    password_encrypted = Column(String)
    smtp_server = Column(String)
    smtp_port = Column(Integer)
    imap_server = Column(String)
    imap_port = Column(Integer)
    
    user_selections = relationship("UserSelectedInboxes", back_populates="inbox", cascade="all, delete-orphan")
    

class Email(Base):
    __tablename__ = "emails"
    
    email_id = Column(Integer, primary_key=True, index=True)
    inbox_id = Column(Integer, ForeignKey("inboxes.inbox_id"))
    sent_from = Column(String)
    sent_to = Column(Text)
    subject = Column(String)
    classification = Column(String)
    body = Column(Text)
    suggested_reply = Column(Text)
    response_text = Column(Text, nullable=True)
    date_received = Column(DateTime, default=datetime.utcnow)
    responded = Column(Boolean, default=False)
    archived = Column(Boolean, default=False)
    
    inbox = relationship("Inbox", backref="emails")


class UserSelectedInboxes(Base):
    __tablename__ = "user_selected_inboxes"
    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    inbox_id = Column(Integer, ForeignKey("inboxes.inbox_id"), primary_key=True)
    
    user = relationship("User", back_populates="selected_inboxes")
    inbox = relationship("Inbox", back_populates="user_selections")


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime, index=True)
    

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    
    user_associations = relationship("UserSelectedCategories", back_populates="category", cascade="all, delete-orphan")


class UserSelectedCategories(Base):
    __tablename__ = "user_selected_categories"
    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), primary_key=True)

    user = relationship("User", back_populates="selected_categories")
    category = relationship("Category", back_populates="user_associations")

