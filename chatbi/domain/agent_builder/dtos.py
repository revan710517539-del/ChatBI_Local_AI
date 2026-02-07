from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AgentProfileDTO(BaseModel):
    id: str
    name: str
    scene: str
    description: Optional[str] = None
    system_prompt: str
    llm_source_id: Optional[str] = None
    enable_rag: bool = True
    enable_sql_tool: bool = True
    enable_rule_validation: bool = True
    created_at: datetime
    updated_at: datetime


class AgentProfileCreateDTO(BaseModel):
    name: str
    scene: str = "loan_general"
    description: Optional[str] = None
    system_prompt: str
    llm_source_id: Optional[str] = None
    enable_rag: bool = True
    enable_sql_tool: bool = True
    enable_rule_validation: bool = True


class AgentProfileUpdateDTO(BaseModel):
    name: Optional[str] = None
    scene: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    llm_source_id: Optional[str] = None
    enable_rag: Optional[bool] = None
    enable_sql_tool: Optional[bool] = None
    enable_rule_validation: Optional[bool] = None
