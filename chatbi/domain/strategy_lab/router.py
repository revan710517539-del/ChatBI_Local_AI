from __future__ import annotations

from fastapi import APIRouter, Query

from chatbi.domain.strategy_lab.dtos import (
    StrategyExperimentCreateDTO,
    StrategyExperimentStatusDTO,
)
from chatbi.domain.strategy_lab.service import StrategyLabService
from chatbi.middleware.standard_response import StandardResponse

router = APIRouter(prefix="/api/v1/strategy-lab", tags=["Strategy Lab"])


@router.get("/summary")
async def get_summary() -> StandardResponse[dict]:
    service = StrategyLabService()
    return StandardResponse(status="success", message="Strategy lab summary", data=service.summary())


@router.get("/experiments")
async def list_experiments(limit: int = Query(100, ge=1, le=500)) -> StandardResponse[list[dict]]:
    service = StrategyLabService()
    return StandardResponse(
        status="success",
        message="Experiments fetched",
        data=service.list_experiments(limit=limit),
    )


@router.get("/experiments/{experiment_id}")
async def get_experiment(experiment_id: str) -> StandardResponse[dict]:
    service = StrategyLabService()
    return StandardResponse(
        status="success",
        message="Experiment fetched",
        data=service.get_experiment(experiment_id),
    )


@router.get("/experiments/{experiment_id}/trend")
async def get_experiment_trend(experiment_id: str) -> StandardResponse[list[dict]]:
    service = StrategyLabService()
    return StandardResponse(
        status="success",
        message="Experiment trend fetched",
        data=service.get_experiment_trend(experiment_id),
    )


@router.post("/experiments/from-strategy")
async def create_from_strategy(payload: StrategyExperimentCreateDTO) -> StandardResponse[dict]:
    service = StrategyLabService()
    return StandardResponse(
        status="success",
        message="Experiment created",
        data=service.create_from_strategy(
            strategy_id=payload.strategy_id,
            name=payload.name,
            sample_size_control=payload.sample_size_control,
            sample_size_treatment=payload.sample_size_treatment,
            duration_days=payload.duration_days,
        ),
    )


@router.put("/experiments/{experiment_id}/status")
async def update_status(experiment_id: str, payload: StrategyExperimentStatusDTO) -> StandardResponse[dict]:
    service = StrategyLabService()
    return StandardResponse(
        status="success",
        message="Experiment status updated",
        data=service.update_status(experiment_id, payload.status),
    )
