from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from chatbi.domain.ai_config.models import (
    DEFAULT_DASHBOARD_PROMPT,
    DEFAULT_DATA_DISCUSS_PROMPT,
    SceneType,
)


class AIConfigRepository:
    def __init__(self) -> None:
        self.base_dir = Path(os.getcwd())
        self.config_dir = self.base_dir / "runs"
        self.config_path = self.config_dir / "ai_config.json"
        self.rag_dir = self.config_dir / "rag_knowledge"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.rag_dir.mkdir(parents=True, exist_ok=True)
        self._bootstrap()
        self._ensure_defaults()

    def _bootstrap(self) -> None:
        if self.config_path.exists():
            return
        now = datetime.utcnow().isoformat()
        default_id = str(uuid4())
        data = {
            "llm_sources": [
                {
                    "id": default_id,
                    "name": "Ollama Local (default)",
                    "provider": "ollama",
                    "base_url": "http://127.0.0.1:11434/v1",
                    "model": "qwen3-4B-instruct-2507_q8",
                    "api_key": "ollama",
                    "description": "Local Ollama OpenAI-compatible endpoint",
                    "is_default": True,
                    "enabled": True,
                    "capability": "chat",
                    "created_at": now,
                    "updated_at": now,
                }
            ],
            "scene_prompts": {
                SceneType.DASHBOARD.value: DEFAULT_DASHBOARD_PROMPT,
                SceneType.DATA_DISCUSS.value: DEFAULT_DATA_DISCUSS_PROMPT,
            },
            "scene_llm_binding": {
                SceneType.DASHBOARD.value: default_id,
                SceneType.DATA_DISCUSS.value: default_id,
            },
            "model_capabilities": {
                "chat": "qwen3-4B-instruct-2507_q8",
                "vision": "minicpm-v4",
                "table": "TableGPT2-7B",
                "embedding": "bge-m3",
            },
            "active_runtime_model": None,
        }
        self._save(data)

    def _ensure_defaults(self) -> None:
        cfg = self._load()
        changed = False
        if "model_capabilities" not in cfg:
            cfg["model_capabilities"] = {
                "chat": "qwen3-4B-instruct-2507_q8",
                "vision": "minicpm-v4",
                "table": "TableGPT2-7B",
                "embedding": "bge-m3",
            }
            changed = True
        if "active_runtime_model" not in cfg:
            cfg["active_runtime_model"] = None
            changed = True
        for src in cfg.get("llm_sources", []):
            if "capability" not in src:
                src["capability"] = "chat"
                changed = True
            if src.get("model") == "qwen2.5:7b":
                src["model"] = "qwen3-4B-instruct-2507_q8"
                changed = True
        if changed:
            self._save(cfg)

    def _load(self) -> dict[str, Any]:
        with self.config_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: dict[str, Any]) -> None:
        with self.config_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def read_config(self) -> dict[str, Any]:
        return self._load()

    def write_config(self, data: dict[str, Any]) -> None:
        self._save(data)

    def list_rag_files(self) -> list[Path]:
        return sorted(
            [p for p in self.rag_dir.iterdir() if p.is_file()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

    def rag_path(self, filename: str) -> Path:
        return self.rag_dir / filename
