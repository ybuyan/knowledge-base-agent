from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class Source(BaseModel):
    id: str
    filename: str
    page: Optional[int] = None
    paragraph: Optional[str] = None
    content: str


class MessageCreate(BaseModel):
    role: str
    content: str
    sources: Optional[List[Source]] = None


class MessageResponse(BaseModel):
    id: str = Field(alias="_id")
    session_id: str
    role: str
    content: str
    sources: Optional[List[Source]] = None
    created_at: datetime
    
    class Config:
        populate_by_name = True


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


class SessionListResponse(BaseModel):
    id: str = Field(alias="_id")
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message: Optional[str] = None
    is_archived: bool = False
    
    class Config:
        populate_by_name = True


class SessionSearchRequest(BaseModel):
    keyword: str = ""
    include_archived: bool = False


class SessionStatsResponse(BaseModel):
    total_sessions: int
    archived_sessions: int
    today_sessions: int
    week_sessions: int
    total_messages: int


class ChatRequest(BaseModel):
    question: str
    session_id: str


class ChatStreamRequest(BaseModel):
    question: str
    session_id: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source] = []
    session_id: str
