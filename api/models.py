from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from ulid import ulid
from datetime import datetime
from api.database import Base

class Conversation(Base):
    __tablename__ = 'conversations'
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(ulid()))
    title: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Message(Base):
    __tablename__ = 'messages'
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(ulid()))
    conversation_id: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)  # 'user', 'assistant', 'tool'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(3072), nullable=True)  # OpenAI text-embedding-3-large
    tool_name: Mapped[str] = mapped_column(String, nullable=True)
    tool_call_id: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)