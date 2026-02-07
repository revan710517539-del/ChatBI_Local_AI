from __future__ import annotations

from fastapi import APIRouter
from fastapi import Query

from chatbi.domain.agent_builder.dtos import (
    AgentProfileCreateDTO,
    AgentProfileUpdateDTO,
)
from chatbi.domain.agent_builder.service import AgentBuilderService
from chatbi.middleware.standard_response import StandardResponse

router = APIRouter(prefix="/api/v1/agent-builder", tags=["Agent Builder"])


@router.get("/profiles")
async def list_profiles() -> StandardResponse[list[dict]]:
    service = AgentBuilderService()
    return StandardResponse(
        status="success",
        message="Agent profiles fetched",
        data=service.list_profiles(),
    )


@router.post("/profiles")
async def create_profile(payload: AgentProfileCreateDTO) -> StandardResponse[dict]:
    service = AgentBuilderService()
    return StandardResponse(
        status="success",
        message="Agent profile created",
        data=service.create_profile(payload),
    )


@router.put("/profiles/{profile_id}")
async def update_profile(
    profile_id: str, payload: AgentProfileUpdateDTO
) -> StandardResponse[dict]:
    service = AgentBuilderService()
    return StandardResponse(
        status="success",
        message="Agent profile updated",
        data=service.update_profile(profile_id, payload),
    )


@router.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: str) -> StandardResponse[dict]:
    service = AgentBuilderService()
    service.delete_profile(profile_id)
    return StandardResponse(
        status="success",
        message="Agent profile deleted",
        data={"id": profile_id},
    )


@router.get("/profiles/{profile_id}/logs")
async def get_execution_logs(
    profile_id: str, limit: int = Query(100, ge=1, le=1000)
) -> StandardResponse[list[dict]]:
    service = AgentBuilderService()
    return StandardResponse(
        status="success",
        message="Execution logs fetched",
        data=service.list_execution_logs(profile_id=profile_id, limit=limit),
    )


@router.delete("/profiles/{profile_id}/logs")
async def clear_execution_logs(profile_id: str) -> StandardResponse[dict]:
    service = AgentBuilderService()
    service.clear_execution_logs(profile_id=profile_id)
    return StandardResponse(
        status="success",
        message="Execution logs cleared",
        data={"id": profile_id},
    )
