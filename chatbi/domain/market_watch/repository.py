from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


class MarketWatchRepository:
    def __init__(self) -> None:
        base = Path(os.getcwd()) / "runs"
        base.mkdir(parents=True, exist_ok=True)
        self.path = base / "market_watch_store.json"
        self._bootstrap()

    def _bootstrap(self) -> None:
        if self.path.exists():
            return
        now = datetime.utcnow().isoformat()
        data = {
            "sources": [
                {
                    "id": str(uuid4()),
                    "name": "Bing News - 贷款新闻",
                    "category": "news",
                    "url": "https://www.bing.com/news/search?q=%E9%93%B6%E8%A1%8C+%E8%B4%B7%E6%AC%BE+%E6%96%B0%E9%97%BB&format=rss",
                    "enabled": True,
                },
                {
                    "id": str(uuid4()),
                    "name": "Bing News - 贷款政策",
                    "category": "policy",
                    "url": "https://www.bing.com/news/search?q=%E8%B4%B7%E6%AC%BE+%E7%9B%91%E7%AE%A1+%E6%94%BF%E7%AD%96+%E9%93%B6%E8%A1%8C&format=rss",
                    "enabled": True,
                },
                {
                    "id": str(uuid4()),
                    "name": "Bing News - 贷款产品",
                    "category": "product",
                    "url": "https://www.bing.com/news/search?q=%E9%93%B6%E8%A1%8C+%E4%BF%A1%E8%B4%B7+%E4%BA%A7%E5%93%81+%E5%88%9B%E6%96%B0&format=rss",
                    "enabled": True,
                },
            ],
            "snapshot": {
                "fetched_at": now,
                "items": {
                    "news": [],
                    "policy": [],
                    "product": [],
                },
            },
        }
        self.save(data)

    def load(self) -> dict[str, Any]:
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, data: dict[str, Any]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
