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
    is_favorite: bool = False
    is_registered: bool = False
    display_name: Optional[str] = None


class ScanDirectory(BaseModel):
    """A directory being scanned for projects."""

    path: str
    project_count: int = 0


class ProjectRegistration(BaseModel):
    """Request to register a project."""

    path: str
    display_name: Optional[str] = None


class ProjectConfigResponse(BaseModel):
    """Response with project configuration."""

    scan_directories: list[str]
    registered_count: int
    favorites_count: int


class Memory(BaseModel):
    """Memory record from the database."""

    id: str
    content: str
    context: Optional[str] = None
    memory_type: str = Field(default="other", validation_alias="type")
    status: str = "fresh"
    importance_score: int = 50
    access_count: int = 0
    created_at: datetime
    last_accessed: Optional[datetime] = None
    tags: list[str] = []

    model_config = {"populate_by_name": True}


class MemoryStats(BaseModel):
    """Statistics about memories in a database."""

    total_count: int
    by_type: dict[str, int]
    by_status: dict[str, int]
    avg_importance: float
    total_access_count: int
    tags: list[dict[str, int | str]]


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


class AggregateMemoryRequest(BaseModel):
    """Request for aggregate memory data across projects."""

    projects: list[str] = Field(..., description="List of project db paths")
    filters: Optional[FilterParams] = None


class AggregateStatsRequest(BaseModel):
    """Request for aggregate statistics."""

    projects: list[str] = Field(..., description="List of project db paths")


class AggregateStatsResponse(BaseModel):
    """Aggregate statistics across multiple projects."""

    total_count: int
    total_access_count: int
    avg_importance: float
    by_type: dict[str, int]
    by_status: dict[str, int]
    project_count: int


class AggregateChatRequest(BaseModel):
    """Request for chat across multiple projects."""

    projects: list[str] = Field(..., description="List of project db paths")
    question: str = Field(..., min_length=1, max_length=2000)
    max_memories_per_project: int = Field(default=5, ge=1, le=20)


class Activity(BaseModel):
    """Activity log record."""

    id: str
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
    # Command analytics fields
    command_name: Optional[str] = None
    command_scope: Optional[str] = None
    mcp_server: Optional[str] = None
    skill_name: Optional[str] = None
    # Natural language summary fields
    summary: Optional[str] = None
    summary_detail: Optional[str] = None


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


class MemoryCreateRequest(BaseModel):
    """Create request for a new memory."""

    content: str = Field(..., min_length=1, max_length=50000)
    memory_type: str = Field(default="general")
    context: Optional[str] = None
    importance_score: int = Field(default=50, ge=1, le=100)
    tags: list[str] = Field(default_factory=list)


class MemoryUpdate(BaseModel):
    """Update request for a memory."""

    content: Optional[str] = None
    context: Optional[str] = None
    memory_type: Optional[str] = Field(None, validation_alias="type")
    status: Optional[str] = None
    importance_score: Optional[int] = Field(None, ge=1, le=100)
    tags: Optional[list[str]] = None

    model_config = {"populate_by_name": True}


class WSEvent(BaseModel):
    """WebSocket event message."""

    event_type: str
    data: dict
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    """Request for the chat endpoint."""

    question: str = Field(..., min_length=1, max_length=2000)
    max_memories: int = Field(default=10, ge=1, le=50)


class ChatSource(BaseModel):
    """Source memory reference in chat response."""

    id: str
    type: str
    content_preview: str
    tags: list[str]
    project_path: Optional[str] = None
    project_name: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from the chat endpoint."""

    answer: str
    sources: list[ChatSource]
    error: Optional[str] = None


class ConversationMessage(BaseModel):
    """A message in a conversation."""

    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str


class ConversationSaveRequest(BaseModel):
    """Request to save a conversation as memory."""

    messages: list[ConversationMessage]
    referenced_memory_ids: Optional[list[str]] = None
    importance: Optional[int] = Field(default=60, ge=1, le=100)


class ConversationSaveResponse(BaseModel):
    """Response after saving a conversation."""

    memory_id: str
    summary: str


# --- Image Generation Models ---


class SingleImageRequestModel(BaseModel):
    """Request for a single image in a batch."""
    preset: str = "custom"  # Maps to ImagePreset enum
    custom_prompt: str = ""
    aspect_ratio: str = "16:9"
    image_size: str = "2K"


class BatchImageGenerationRequest(BaseModel):
    """Request for generating multiple images."""
    images: list[SingleImageRequestModel]  # 1, 2, or 4 images
    memory_ids: list[str] = []
    chat_messages: list[dict] = []  # Recent chat for context
    use_search_grounding: bool = False


class ImageRefineRequest(BaseModel):
    """Request for refining an existing image."""
    image_id: str
    refinement_prompt: str
    aspect_ratio: Optional[str] = None
    image_size: Optional[str] = None


class SingleImageResponseModel(BaseModel):
    """Response for a single generated image."""
    success: bool
    image_data: Optional[str] = None  # Base64 encoded
    text_response: Optional[str] = None
    thought_signature: Optional[str] = None
    image_id: Optional[str] = None
    error: Optional[str] = None
    index: int = 0


class BatchImageGenerationResponse(BaseModel):
    """Response for batch image generation."""
    success: bool
    images: list[SingleImageResponseModel] = []
    errors: list[str] = []
