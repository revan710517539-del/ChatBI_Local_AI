from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, Query

from chatbi.dependencies import RepositoryDependency
from chatbi.domain.dashboard.service import DashboardService
from chatbi.domain.datasource.repository import DatasourceRepository
from chatbi.middleware.standard_response import StandardResponse

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])
DatasourceRepoDep = RepositoryDependency(DatasourceRepository, use_async_session=True)


class MetricEngineQueryDTO(BaseModel):
    datasource_id: Optional[str] = None
    metric_keys: list[str] = Field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    channels: Optional[list[str]] = None
    customer_segments: Optional[list[str]] = None
    customer_groups: Optional[list[str]] = None
    loan_product: Optional[str] = None


@router.get("/loan-kpis")
async def get_loan_kpis(
    datasource_id: Optional[str] = Query(None),
    repo: DatasourceRepository = Depends(DatasourceRepoDep),
) -> StandardResponse[dict]:
    service = DashboardService(datasource_repo=repo)
    data = await service.get_loan_kpis(datasource_id=datasource_id)
    return StandardResponse(
        status="success",
        message="Loan KPI fetched",
        data=data,
    )


@router.get("/metric-catalog")
async def get_metric_catalog() -> StandardResponse[dict]:
    return StandardResponse(
        status="success",
        message="Metric catalog fetched",
        data=DashboardService.get_metric_catalog(),
    )


@router.get("/indicator-definitions")
async def get_indicator_definitions() -> StandardResponse[list[dict]]:
    return StandardResponse(
        status="success",
        message="Indicator definitions fetched",
        data=DashboardService.get_indicator_definitions(),
    )


@router.post("/metric-engine/query")
async def metric_engine_query(
    payload: MetricEngineQueryDTO,
    repo: DatasourceRepository = Depends(DatasourceRepoDep),
) -> StandardResponse[dict]:
    service = DashboardService(datasource_repo=repo)
    data = await service.query_metrics_with_filters(
        datasource_id=payload.datasource_id,
        metric_keys=payload.metric_keys,
        start_date=payload.start_date,
        end_date=payload.end_date,
        channels=payload.channels,
        customer_segments=payload.customer_segments,
        customer_groups=payload.customer_groups,
        loan_product=payload.loan_product,
    )
    return StandardResponse(
        status="success",
        message="Metric engine query done",
        data=data,
    )
