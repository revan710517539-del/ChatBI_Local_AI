from __future__ import annotations

from pydantic import BaseModel


class StrategyExperimentCreateDTO(BaseModel):
    strategy_id: str
    name: str | None = None
    sample_size_control: int = 3000
    sample_size_treatment: int = 3000
    duration_days: int = 14


class StrategyExperimentStatusDTO(BaseModel):
    status: str
