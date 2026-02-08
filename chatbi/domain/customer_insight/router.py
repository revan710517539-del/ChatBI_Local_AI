from __future__ import annotations

from fastapi import APIRouter, HTTPException

from chatbi.domain.customer_insight.service import CustomerInsightService
from chatbi.middleware.standard_response import StandardResponse

router = APIRouter(prefix="/api/v1/customer-insight", tags=["Customer Insight"])


@router.get("/customers")
async def list_customers() -> StandardResponse[list[dict]]:
    service = CustomerInsightService()
    return StandardResponse(status="success", message="Customers fetched", data=service.list_customers())


@router.get("/customers/{customer_id}")
async def get_customer(customer_id: str) -> StandardResponse[dict]:
    service = CustomerInsightService()
    item = service.get_customer(customer_id)
    if not item:
        raise HTTPException(status_code=404, detail="Customer not found")
    return StandardResponse(status="success", message="Customer fetched", data=item)


@router.get("/segments")
async def list_segments() -> StandardResponse[list[dict]]:
    service = CustomerInsightService()
    return StandardResponse(status="success", message="Segments fetched", data=service.list_segments())


@router.get("/segments/{segment_id}")
async def get_segment(segment_id: str) -> StandardResponse[dict]:
    service = CustomerInsightService()
    item = service.get_segment(segment_id)
    if not item:
        raise HTTPException(status_code=404, detail="Segment not found")
    return StandardResponse(status="success", message="Segment fetched", data=item)
