from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Source(BaseModel):
    id: str
    filename: str
    page: Optional[int] = None
    paragraph: Optional[str] = None
    content: str


class SessionCreate(BaseModel):
    title: str = "新对话"


class SessionUpdate(BaseModel):
    title: str


class SessionArchiveRequest(BaseModel):
    is_archived: bool = True


class SessionResponse(BaseModel):
    id: str = Field(alias="_id")
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message: Optional[str] = None
    is_archived: bool = False

    class Config:
        populate_by_name = True


class SessionStatsResponse(BaseModel):
    total_sessions: int
    archived_sessions: int
    today_sessions: int
    week_sessions: int
    total_messages: int


class ChatStreamRequest(BaseModel):
    question: str
    session_id: str
