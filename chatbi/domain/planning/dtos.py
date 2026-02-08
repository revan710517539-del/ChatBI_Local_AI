from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class PlanningRuleUpdateDTO(BaseModel):
    rules: list[dict[str, Any]]


class PlanningChainUpdateDTO(BaseModel):
    chains: list[dict[str, Any]]


class PlanRequestDTO(BaseModel):
    question: str
    scene: str = "data_discuss"
    loan_type: str | None = None


class PlanExecutionRecordDTO(BaseModel):
    plan_id: str
    status: str = "planned"
    note: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PlanExecutionStartDTO(BaseModel):
    plan_id: str | None = None
    question: str | None = None
    scene: str = "data_discuss"
    loan_type: str | None = None
    auto_start: bool = True


class PlanTaskActionDTO(BaseModel):
    task_id: str
    action: Literal["start", "complete", "fail", "retry", "skip"]
    note: str | None = None


class PlanExecutionRunDTO(BaseModel):
    max_steps: int = 20
