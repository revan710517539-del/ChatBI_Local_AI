from __future__ import annotations

from fastapi import APIRouter, Query

from chatbi.domain.market_watch.service import MarketWatchService
from chatbi.middleware.standard_response import StandardResponse

router = APIRouter(prefix="/api/v1/market-watch", tags=["Market Watch"])


@router.get("/sources")
async def list_sources() -> StandardResponse[list[dict]]:
    service = MarketWatchService()
    return StandardResponse(status="success", message="Market sources fetched", data=service.list_sources())


@router.get("/snapshot")
async def get_snapshot(
    limit: int = Query(8, ge=1, le=30),
    force_refresh: bool = Query(False),
) -> StandardResponse[dict]:
    service = MarketWatchService()
    return StandardResponse(
        status="success",
        message="Market snapshot fetched",
        data=service.get_snapshot(limit=limit, force_refresh=force_refresh),
    )


@router.get("/analysis")
async def market_analysis(
    limit: int = Query(8, ge=1, le=30),
    force_refresh: bool = Query(False),
) -> StandardResponse[dict]:
    service = MarketWatchService()
    return StandardResponse(
        status="success",
        message="Market analysis generated",
        data=service.market_analysis(limit=limit, force_refresh=force_refresh),
    )


@router.post("/refresh")
async def refresh_snapshot(limit: int = Query(8, ge=1, le=30)) -> StandardResponse[dict]:
    service = MarketWatchService()
    return StandardResponse(
        status="success",
        message="Market snapshot refreshed",
        data=service.refresh_snapshot(limit=limit),
    )
