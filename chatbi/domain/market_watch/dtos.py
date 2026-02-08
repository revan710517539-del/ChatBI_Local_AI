from __future__ import annotations

from pydantic import BaseModel


class MarketWatchQueryDTO(BaseModel):
    limit: int = 8
    force_refresh: bool = False
