"""
数据库 ORM 模型
使用 SQLAlchemy/SQLModel 存储用户与日志
"""
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    GUEST = "guest"


class DocumentStatus(str, Enum):
    QUEUED = "QUEUED"
    INDEXING = "INDEXING"
    READY = "READY"
    ERROR = "ERROR"


class User(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    roles: str = Field(default="employee")
    department: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    chat_sessions: List["ChatSession"] = Relationship(back_populates="user")
    audit_logs: List["AuditLog"] = Relationship(back_populates="user")


class Document(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    filename: str
    file_path: str
    file_size: int
    file_type: str
    status: DocumentStatus = Field(default=DocumentStatus.QUEUED)
    access_level: str = Field(default="public")
    chunk_count: int = Field(default=0)
    error_message: Optional[str] = Field(default=None)
    uploaded_by: Optional[str] = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    audit_logs: List["AuditLog"] = Relationship(back_populates="document")


class ChatSession(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: Optional[str] = Field(default=None, foreign_key="user.id")
    title: str = Field(default="新对话")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: Optional[User] = Relationship(back_populates="chat_sessions")
    messages: List["ChatMessage"] = Relationship(back_populates="session")


class ChatMessage(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    session_id: Optional[str] = Field(default=None, foreign_key="chatsession.id")
    role: str
    content: str
    sources: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    session: Optional[ChatSession] = Relationship(back_populates="messages")


class AuditLog(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: Optional[str] = Field(default=None, foreign_key="user.id")
    document_id: Optional[str] = Field(default=None, foreign_key="document.id")
    action: str
    resource_type: str
    resource_id: Optional[str] = Field(default=None)
    details: Optional[str] = Field(default=None)
    ip_address: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: Optional[User] = Relationship(back_populates="audit_logs")
    document: Optional[Document] = Relationship(back_populates="audit_logs")


class LLMCallLog(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: Optional[str] = Field(default=None)
    session_id: Optional[str] = Field(default=None)
    model: str
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    latency_ms: int = Field(default=0)
    status: str = Field(default="success")
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SystemConfig(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True)
    value: str
    description: Optional[str] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = Field(default=None)
