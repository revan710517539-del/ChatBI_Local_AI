from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MCPServerCreateDTO(BaseModel):
    name: str
    endpoint: str
    description: str | None = None
    enabled: bool = True
    capabilities: list[str] = Field(default_factory=list)


class MCPServerUpdateDTO(BaseModel):
    name: str | None = None
    endpoint: str | None = None
    description: str | None = None
    enabled: bool | None = None
    capabilities: list[str] | None = None


class SkillCreateDTO(BaseModel):
    name: str
    category: str = "loan_ops"
    description: str | None = None
    enabled: bool = True
    trigger: str | None = None


class SkillUpdateDTO(BaseModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None
    enabled: bool | None = None
    trigger: str | None = None


class EmailConfigUpdateDTO(BaseModel):
    sender: str | None = None
    recipient: str | None = None
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_user: str | None = None
    smtp_password: str | None = None
    use_tls: bool | None = None


class StrategyGenerateDTO(BaseModel):
    topic: str
    loan_type: str = "mixed"
    audience: str = "bank_ops"
    kpi_snapshot: dict[str, Any] = Field(default_factory=dict)


class StrategySendDTO(BaseModel):
    strategy_id: str


class StrategyApprovalDTO(BaseModel):
    reply_text: str = "AGREE"
    execute: bool = True


class StrategyRefineDTO(BaseModel):
    discussion: str
    operator: str = "human"
