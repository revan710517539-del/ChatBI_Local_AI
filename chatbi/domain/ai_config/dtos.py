from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from chatbi.domain.ai_config.models import SceneType


class LLMSourceCreateDTO(BaseModel):
    name: str
    provider: str = "ollama"
    base_url: str = "http://127.0.0.1:11434/v1"
    model: str
    api_key: Optional[str] = None
    description: Optional[str] = None
    is_default: bool = False
    enabled: bool = True
    capability: str = "chat"


class LLMSourceUpdateDTO(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    enabled: Optional[bool] = None
    capability: Optional[str] = None


class LLMSourceDTO(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    provider: str = "ollama"
    base_url: str
    model: str
    api_key: Optional[str] = None
    description: Optional[str] = None
    is_default: bool = False
    enabled: bool = True
    capability: str = "chat"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PromptUpdateDTO(BaseModel):
    scene: SceneType
    prompt: str


class PromptDTO(BaseModel):
    scene: SceneType
    prompt: str


class SceneModelBindingDTO(BaseModel):
    scene: SceneType
    llm_source_id: str


class RagDocumentDTO(BaseModel):
    id: str
    filename: str
    path: str
    size: int
    updated_at: datetime


class CapabilityModelUpdateDTO(BaseModel):
    capability: str
    model: str


class TableAnalyzeDTO(BaseModel):
    prompt: str
    table_text: str
