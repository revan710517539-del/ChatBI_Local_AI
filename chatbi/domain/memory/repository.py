from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class MemoryRepository:
    def __init__(self) -> None:
        base = Path(os.getcwd()) / "runs"
        base.mkdir(parents=True, exist_ok=True)
        self.path = base / "memory_store.json"
        self._bootstrap()

    def _bootstrap(self) -> None:
        if self.path.exists():
            return
        self._save(
            {
                "settings": {
                    "enabled": True,
                    "retention_days": 90,
                    "max_records": 5000,
                    "summary_window": 8,
                    "semantic_enhance": True,
                    "weight_recent": 0.45,
                    "weight_relevance": 0.55,
                    "capture_text": True,
                    "capture_voice": True,
                    "capture_files": True,
                    "capture_images": True,
                    "capture_metric_actions": True,
                },
                "events": [],
            }
        )

    def _load(self) -> dict[str, Any]:
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: dict[str, Any]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def read(self) -> dict[str, Any]:
        return self._load()

    def write(self, data: dict[str, Any]) -> None:
        self._save(data)
