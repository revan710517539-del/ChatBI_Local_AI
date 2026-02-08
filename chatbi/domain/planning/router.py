from __future__ import annotations

from fastapi import APIRouter, Query

from chatbi.domain.planning.dtos import (
    PlanExecutionRecordDTO,
    PlanExecutionRunDTO,
    PlanExecutionStartDTO,
    PlanRequestDTO,
    PlanTaskActionDTO,
    PlanningChainUpdateDTO,
    PlanningRuleUpdateDTO,
)
from chatbi.domain.planning.service import PlanningService
from chatbi.middleware.standard_response import StandardResponse

router = APIRouter(prefix="/api/v1/planning", tags=["Planning"])


@router.get("/rules")
async def list_rules() -> StandardResponse[list[dict]]:
    service = PlanningService()
    return StandardResponse(
        status="success", message="Planning rules fetched", data=service.list_rules()
    )


@router.put("/rules")
async def update_rules(payload: PlanningRuleUpdateDTO) -> StandardResponse[list[dict]]:
    service = PlanningService()
    return StandardResponse(
        status="success",
        message="Planning rules updated",
        data=service.update_rules(payload.rules),
    )


@router.get("/chains")
async def list_chains() -> StandardResponse[list[dict]]:
    service = PlanningService()
    return StandardResponse(
        status="success", message="Planning chains fetched", data=service.list_chains()
    )


@router.put("/chains")
async def update_chains(payload: PlanningChainUpdateDTO) -> StandardResponse[list[dict]]:
    service = PlanningService()
    return StandardResponse(
        status="success",
        message="Planning chains updated",
        data=service.update_chains(payload.chains),
    )


@router.post("/plan")
async def build_plan(payload: PlanRequestDTO) -> StandardResponse[dict]:
    service = PlanningService()
    return StandardResponse(
        status="success",
        message="Plan generated",
        data=service.build_plan(payload.question, payload.scene, payload.loan_type),
    )


@router.get("/plans")
async def list_plans(limit: int = Query(100, ge=1, le=500)) -> StandardResponse[list[dict]]:
    service = PlanningService()
    return StandardResponse(
        status="success",
        message="Plan history fetched",
        data=service.list_plan_history(limit=limit),
    )


@router.post("/executions/start")
async def start_execution(payload: PlanExecutionStartDTO) -> StandardResponse[dict]:
    service = PlanningService()
    data = service.start_execution(
        plan_id=payload.plan_id,
        question=payload.question,
        scene=payload.scene,
        loan_type=payload.loan_type,
        auto_start=payload.auto_start,
    )
    return StandardResponse(status="success", message="Execution started", data=data)


@router.get("/executions")
async def list_executions(limit: int = Query(100, ge=1, le=500)) -> StandardResponse[list[dict]]:
    service = PlanningService()
    return StandardResponse(
        status="success",
        message="Executions fetched",
        data=service.list_executions(limit=limit),
    )


@router.get("/executions/{execution_id}")
async def get_execution(execution_id: str) -> StandardResponse[dict]:
    service = PlanningService()
    return StandardResponse(
        status="success",
        message="Execution fetched",
        data=service.get_execution(execution_id),
    )


@router.post("/executions/{execution_id}/task-action")
async def task_action(execution_id: str, payload: PlanTaskActionDTO) -> StandardResponse[dict]:
    service = PlanningService()
    return StandardResponse(
        status="success",
        message="Task action applied",
        data=service.task_action(
            execution_id=execution_id,
            task_id=payload.task_id,
            action=payload.action,
            note=payload.note,
        ),
    )


@router.post("/executions/{execution_id}/tick")
async def tick_execution(execution_id: str) -> StandardResponse[dict]:
    service = PlanningService()
    return StandardResponse(
        status="success",
        message="Execution advanced",
        data=service.tick_execution(execution_id),
    )


@router.post("/executions/{execution_id}/run")
async def run_execution(execution_id: str, payload: PlanExecutionRunDTO) -> StandardResponse[dict]:
    service = PlanningService()
    return StandardResponse(
        status="success",
        message="Execution run completed",
        data=service.run_execution(execution_id, payload.max_steps),
    )


@router.post("/execution")
async def record_execution(payload: PlanExecutionRecordDTO) -> StandardResponse[dict]:
    service = PlanningService()
    return StandardResponse(
        status="success",
        message="Execution record created",
        data=service.record_execution(payload),
    )


@router.get("/execution")
async def list_execution_logs(
    limit: int = Query(200, ge=1, le=1000),
    execution_id: str | None = Query(None),
) -> StandardResponse[list[dict]]:
    service = PlanningService()
    return StandardResponse(
        status="success",
        message="Execution logs fetched",
        data=service.list_execution_logs(limit=limit, execution_id=execution_id),
    )
