from __future__ import annotations

from typing import Any

from chatbi.domain.customer_insight.repository import CustomerInsightRepository


class CustomerInsightService:
    def __init__(self, repo: CustomerInsightRepository | None = None) -> None:
        self.repo = repo or CustomerInsightRepository()

    def list_customers(self) -> list[dict[str, Any]]:
        return self.repo.load().get("customers", [])

    def get_customer(self, customer_id: str) -> dict[str, Any] | None:
        for item in self.list_customers():
            if item.get("customer_id") == customer_id:
                return item
        return None

    def list_segments(self) -> list[dict[str, Any]]:
        return self.repo.load().get("segments", [])

    def get_segment(self, segment_id: str) -> dict[str, Any] | None:
        for item in self.list_segments():
            if item.get("segment_id") == segment_id:
                return item
        return None
