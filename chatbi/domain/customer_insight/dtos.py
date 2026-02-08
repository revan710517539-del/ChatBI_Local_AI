from __future__ import annotations

from pydantic import BaseModel


class CustomerInsightQueryDTO(BaseModel):
    customer_id: str


class SegmentInsightQueryDTO(BaseModel):
    segment_id: str
