from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PlanningRule(BaseModel):
    id: str
    name: str
    enabled: bool = True
    match_keywords: list[str] = Field(default_factory=list)
    split_template: list[str] = Field(default_factory=list)
    preferred_agents: list[str] = Field(default_factory=list)
    toolchain: dict[str, bool] = Field(
        default_factory=lambda: {
            "sql": True,
            "rag": True,
            "rule_validation": True,
        }
    )


class PlanningChain(BaseModel):
    id: str
    name: str
    enabled: bool = True
    mode: str = "a2a_dispatch"
    steps: list[dict[str, Any]] = Field(default_factory=list)


class PlanTask(BaseModel):
    task_id: str
    title: str
    objective: str
    assigned_agent: str
    depends_on: list[str] = Field(default_factory=list)
    tools: dict[str, bool] = Field(default_factory=dict)


class PlanResult(BaseModel):
    plan_id: str
    scene: str
    question: str
    workflow_mode: str
    strategy_focus: str
    tasks: list[PlanTask] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)
