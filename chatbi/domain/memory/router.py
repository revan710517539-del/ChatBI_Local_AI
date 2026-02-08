from __future__ import annotations

from fastapi import APIRouter, Query

from chatbi.domain.memory.dtos import (
    MemoryBuildContextDTO,
    MemoryEventCreateDTO,
    MemorySearchDTO,
    MemorySettingsUpdateDTO,
)
from chatbi.domain.memory.service import MemoryService
from chatbi.middleware.standard_response import StandardResponse

router = APIRouter(prefix="/api/v1/memory", tags=["Memory"])


@router.get("/settings")
async def get_memory_settings():
    service = MemoryService()
    return StandardResponse(
        status="success",
        message="Memory settings fetched",
        data=service.get_settings(),
    )


@router.put("/settings")
async def update_memory_settings(payload: MemorySettingsUpdateDTO):
    service = MemoryService()
    return StandardResponse(
        status="success",
        message="Memory settings updated",
        data=service.update_settings(payload),
    )


@router.post("/events")
async def create_memory_event(payload: MemoryEventCreateDTO):
    service = MemoryService()
    return StandardResponse(
        status="success",
        message="Memory event recorded",
        data=service.record_event(payload),
    )


@router.get("/events")
async def list_memory_events(
    limit: int = Query(100, ge=1, le=2000),
    scene: str | None = Query(None),
    event_type: str | None = Query(None),
):
    service = MemoryService()
    return StandardResponse(
        status="success",
        message="Memory events fetched",
        data=service.list_events(limit=limit, scene=scene, event_type=event_type),
    )


@router.post("/search")
async def search_memory(payload: MemorySearchDTO):
    service = MemoryService()
    return StandardResponse(
        status="success",
        message="Memory search completed",
        data=service.search_events(
            query=payload.query,
            limit=payload.limit,
            scene=payload.scene,
        ),
    )


@router.post("/context")
async def build_memory_context(payload: MemoryBuildContextDTO):
    service = MemoryService()
    return StandardResponse(
        status="success",
        message="Memory context built",
        data={
            "context": service.build_context(
                query=payload.query,
                limit=payload.limit,
                scene=payload.scene,
            )
        },
    )
