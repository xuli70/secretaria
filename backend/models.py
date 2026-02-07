from datetime import datetime, timezone

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship

from backend.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(Text, unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    last_login = Column(DateTime, nullable=True)

    conversations = relationship("Conversation", back_populates="user")
    telegram_contacts = relationship("TelegramContact", back_populates="user")
    google_token = relationship("GoogleToken", back_populates="user", uselist=False)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(Text, default="Nueva conversación")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")
    files = relationship("File", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(Text, nullable=False)  # "user" | "assistant" | "system"
    content = Column(Text, nullable=False)
    model_used = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    conversation = relationship("Conversation", back_populates="messages")
    files = relationship("File", back_populates="message")
    telegram_sends = relationship("TelegramSend", back_populates="message")


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    filename = Column(Text, nullable=False)
    filepath = Column(Text, nullable=False)
    file_type = Column(Text, nullable=True)
    mime_type = Column(Text, nullable=True)
    size_bytes = Column(Integer, nullable=True)
    extracted_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    conversation = relationship("Conversation", back_populates="files")
    message = relationship("Message", back_populates="files")


class TelegramContact(Base):
    __tablename__ = "telegram_contacts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(Text, nullable=False)
    chat_id = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="telegram_contacts")
    sends = relationship("TelegramSend", back_populates="contact")


class TelegramSend(Base):
    __tablename__ = "telegram_sends"

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("telegram_contacts.id"), nullable=False)
    status = Column(Text, default="pending")
    sent_at = Column(DateTime, nullable=True)

    message = relationship("Message", back_populates="telegram_sends")
    contact = relationship("TelegramContact", back_populates="sends")


class GoogleToken(Base):
    __tablename__ = "google_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    encrypted_token = Column(LargeBinary, nullable=False)
    scopes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="google_token")
