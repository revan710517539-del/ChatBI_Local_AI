from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from chatbi.domain.memory.models import EventType


class MemoryEventCreateDTO(BaseModel):
    event_type: EventType
    scene: str = "data_discuss"
    user_id: str = "anonymous"
    user_text: str | None = None
    voice_text: str | None = None
    files: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    metric_action: dict[str, Any] | None = None
    intent: str | None = None
    sql: str | None = None
    result_summary: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemorySettingsUpdateDTO(BaseModel):
    enabled: bool | None = None
    retention_days: int | None = None
    max_records: int | None = None
    summary_window: int | None = None
    semantic_enhance: bool | None = None
    weight_recent: float | None = None
    weight_relevance: float | None = None
    capture_text: bool | None = None
    capture_voice: bool | None = None
    capture_files: bool | None = None
    capture_images: bool | None = None
    capture_metric_actions: bool | None = None


class MemorySearchDTO(BaseModel):
    query: str
    limit: int = 20
    scene: str | None = None


class MemoryBuildContextDTO(BaseModel):
    query: str
    limit: int = 6
    scene: str | None = None
