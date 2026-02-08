from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


EventType = Literal[
    "text_input",
    "voice_input",
    "file_upload",
    "image_upload",
    "metric_action",
    "analysis_result",
]


class MemorySettings(BaseModel):
    enabled: bool = True
    retention_days: int = 90
    max_records: int = 5000
    summary_window: int = 8
    semantic_enhance: bool = True
    weight_recent: float = 0.45
    weight_relevance: float = 0.55
    capture_text: bool = True
    capture_voice: bool = True
    capture_files: bool = True
    capture_images: bool = True
    capture_metric_actions: bool = True


class MemoryEvent(BaseModel):
    id: str
    ts: str
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
