from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from chatbi.domain.agent_builder.dtos import (
    AgentProfileCreateDTO,
    AgentProfileUpdateDTO,
)
from chatbi.domain.agent_builder.repository import AgentBuilderRepository


class AgentBuilderService:
    def __init__(self, repo: AgentBuilderRepository | None = None) -> None:
        self.repo = repo or AgentBuilderRepository()

    def list_profiles(self) -> list[dict]:
        data = self.repo.load()["profiles"]
        for p in data:
            p.setdefault("enable_rag", True)
            p.setdefault("enable_sql_tool", True)
            p.setdefault("enable_rule_validation", True)
        return data

    def get_profile(self, profile_id: str) -> dict | None:
        for p in self.repo.load()["profiles"]:
            if p["id"] == profile_id:
                return p
        return None

    def create_profile(self, payload: AgentProfileCreateDTO) -> dict:
        data = self.repo.load()
        now = datetime.utcnow().isoformat()
        item = {
            "id": str(uuid4()),
            **payload.model_dump(),
            "created_at": now,
            "updated_at": now,
        }
        data["profiles"].append(item)
        self.repo.save(data)
        return item

    def update_profile(self, profile_id: str, payload: AgentProfileUpdateDTO) -> dict:
        data = self.repo.load()
        for p in data["profiles"]:
            if p["id"] != profile_id:
                continue
            p.update(payload.model_dump(exclude_unset=True))
            p["updated_at"] = datetime.utcnow().isoformat()
            self.repo.save(data)
            return p
        raise ValueError(f"Profile not found: {profile_id}")

    def delete_profile(self, profile_id: str) -> None:
        data = self.repo.load()
        old_size = len(data["profiles"])
        data["profiles"] = [p for p in data["profiles"] if p["id"] != profile_id]
        if len(data["profiles"]) == old_size:
            raise ValueError(f"Profile not found: {profile_id}")
        data.setdefault("execution_logs", {}).pop(profile_id, None)
        self.repo.save(data)

    def append_execution_log(self, profile_id: str, log: dict) -> None:
        data = self.repo.load()
        logs = data.setdefault("execution_logs", {}).setdefault(profile_id, [])
        logs.append(log)
        # keep latest logs only
        data["execution_logs"][profile_id] = logs[-1000:]
        self.repo.save(data)

    def list_execution_logs(self, profile_id: str, limit: int = 100) -> list[dict]:
        data = self.repo.load()
        logs = data.setdefault("execution_logs", {}).get(profile_id, [])
        return logs[-limit:][::-1]

    def clear_execution_logs(self, profile_id: str) -> None:
        data = self.repo.load()
        data.setdefault("execution_logs", {})[profile_id] = []
        self.repo.save(data)
