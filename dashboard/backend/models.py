"""Pydantic models for the dashboard API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProjectInfo(BaseModel):
    """Information about a project with omni-cortex database."""

    name: str
    path: str
    db_path: str
    last_modified: Optional[datetime] = None
    memory_count: int = 0
    is_global: bool = False


class Memory(BaseModel):
    """Memory record from the database."""

    id: str
    content: str
    context: Optional[str] = None
    memory_type: str = Field(alias="type")
    status: str = "fresh"
    importance_score: int = 50
    access_count: int = 0
    created_at: datetime
    last_accessed: Optional[datetime] = None
    tags: list[str] = []

    class Config:
        populate_by_name = True


class MemoryStats(BaseModel):
    """Statistics about memories in a database."""

    total_count: int
    by_type: dict[str, int]
    by_status: dict[str, int]
    avg_importance: float
    total_access_count: int
    tags: list[dict[str, int | str]]


class Activity(BaseModel):
    """Activity log record."""

    id: int
    session_id: Optional[str] = None
    event_type: str
    tool_name: Optional[str] = None
    tool_input: Optional[str] = None
    tool_output: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    file_path: Optional[str] = None
    timestamp: datetime


class Session(BaseModel):
    """Session record."""

    id: str
    project_path: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    summary: Optional[str] = None
    activity_count: int = 0


class TimelineEntry(BaseModel):
    """Entry in the timeline view."""

    timestamp: datetime
    entry_type: str  # "memory" or "activity"
    data: dict


class FilterParams(BaseModel):
    """Query filter parameters."""

    memory_type: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[list[str]] = None
    search: Optional[str] = None
    min_importance: Optional[int] = None
    max_importance: Optional[int] = None
    sort_by: str = "last_accessed"
    sort_order: str = "desc"
    limit: int = 50
    offset: int = 0


class WSEvent(BaseModel):
    """WebSocket event message."""

    event_type: str
    data: dict
    timestamp: datetime = Field(default_factory=datetime.now)
