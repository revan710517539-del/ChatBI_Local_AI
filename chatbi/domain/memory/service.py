from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from chatbi.domain.memory.dtos import (
    MemoryEventCreateDTO,
    MemorySettingsUpdateDTO,
)
from chatbi.domain.memory.models import MemoryEvent, MemorySettings
from chatbi.domain.memory.repository import MemoryRepository


class MemoryService:
    def __init__(self, repo: MemoryRepository | None = None) -> None:
        self.repo = repo or MemoryRepository()

    def get_settings(self) -> dict[str, Any]:
        data = self.repo.read()
        return MemorySettings(**data.get("settings", {})).model_dump()

    def update_settings(self, payload: MemorySettingsUpdateDTO) -> dict[str, Any]:
        data = self.repo.read()
        merged = {**data.get("settings", {}), **payload.model_dump(exclude_unset=True)}
        data["settings"] = MemorySettings(**merged).model_dump()
        self.repo.write(data)
        return data["settings"]

    def list_events(self, limit: int = 100, scene: str | None = None, event_type: str | None = None) -> list[dict[str, Any]]:
        data = self.repo.read()
        events = data.get("events", [])
        if scene:
            events = [e for e in events if e.get("scene") == scene]
        if event_type:
            events = [e for e in events if e.get("event_type") == event_type]
        events = sorted(events, key=lambda x: x.get("ts", ""), reverse=True)
        return events[:limit]

    def _should_capture(self, settings: dict[str, Any], event_type: str) -> bool:
        mapping = {
            "text_input": "capture_text",
            "voice_input": "capture_voice",
            "file_upload": "capture_files",
            "image_upload": "capture_images",
            "metric_action": "capture_metric_actions",
            "analysis_result": "capture_text",
        }
        flag = mapping.get(event_type)
        if not flag:
            return True
        return bool(settings.get(flag, True))

    def record_event(self, payload: MemoryEventCreateDTO) -> dict[str, Any]:
        data = self.repo.read()
        settings = MemorySettings(**data.get("settings", {})).model_dump()
        if not settings.get("enabled", True):
            return {"saved": False, "reason": "memory_disabled"}
        if not self._should_capture(settings, payload.event_type):
            return {"saved": False, "reason": "capture_disabled"}

        event = MemoryEvent(
            id=str(uuid.uuid4()),
            ts=datetime.now(timezone.utc).isoformat(),
            **payload.model_dump(),
        ).model_dump()

        events = data.get("events", [])
        events.append(event)

        # retention cleanup
        retention_days = int(settings.get("retention_days", 90))
        min_time = datetime.now(timezone.utc) - timedelta(days=retention_days)
        kept = []
        for e in events:
            try:
                ts = datetime.fromisoformat(e.get("ts"))
                if ts >= min_time:
                    kept.append(e)
            except Exception:
                kept.append(e)

        max_records = int(settings.get("max_records", 5000))
        data["events"] = kept[-max_records:]
        self.repo.write(data)
        return {"saved": True, "event": event}

    @staticmethod
    def _text_of_event(event: dict[str, Any]) -> str:
        parts = [
            event.get("user_text") or "",
            event.get("voice_text") or "",
            event.get("result_summary") or "",
            event.get("sql") or "",
        ]
        m = event.get("metric_action")
        if isinstance(m, dict):
            parts.append(str(m))
        return "\n".join([p for p in parts if p]).lower()

    def search_events(self, query: str, limit: int = 20, scene: str | None = None) -> list[dict[str, Any]]:
        query_l = query.lower().strip()
        if not query_l:
            return []

        events = self.list_events(limit=2000, scene=scene)
        scored: list[tuple[float, dict[str, Any]]] = []
        now = datetime.now(timezone.utc)

        for e in events:
            text = self._text_of_event(e)
            if not text:
                continue
            hit = 1.0 if query_l in text else 0.0
            overlap = len(set(query_l.split()) & set(text.split()))
            try:
                ts = datetime.fromisoformat(e.get("ts"))
                age_days = max((now - ts).total_seconds() / 86400, 0)
            except Exception:
                age_days = 365
            recent_score = max(0.0, 1.0 - age_days / 120)
            score = 0.55 * (hit + overlap * 0.05) + 0.45 * recent_score
            if score > 0.01:
                scored.append((score, e))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:limit]]

    def build_context(self, query: str, limit: int = 6, scene: str | None = None) -> str:
        hits = self.search_events(query=query, limit=limit, scene=scene)
        lines: list[str] = []
        for h in hits:
            ts = h.get("ts", "")
            et = h.get("event_type", "")
            text = h.get("user_text") or h.get("voice_text") or h.get("result_summary") or ""
            if text:
                lines.append(f"[{ts}][{et}] {text[:260]}")
        return "\n".join(lines)
