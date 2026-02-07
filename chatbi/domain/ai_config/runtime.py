from __future__ import annotations

import httpx
import re


class OllamaRuntimeManager:
    def __init__(self, base_url: str = "http://127.0.0.1:11434") -> None:
        self.base_url = base_url.rstrip("/")

    def _client(self) -> httpx.Client:
        return httpx.Client(timeout=60)

    def list_local_models(self) -> list[str]:
        with self._client() as client:
            resp = client.get(f"{self.base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            models = data.get("models", [])
            result: list[str] = []
            for m in models:
                name = m.get("name") or m.get("model")
                if name:
                    result.append(name)
            return result

    @staticmethod
    def _normalize_model_name(name: str) -> str:
        lowered = name.lower().strip()
        lowered = lowered.replace(":latest", "")
        if "/" in lowered:
            lowered = lowered.split("/", 1)[1]
        return re.sub(r"[^a-z0-9]+", "", lowered)

    def resolve_model_name(self, model: str) -> str:
        local_models = self.list_local_models()
        if not local_models:
            return model
        if model in local_models:
            return model
        normalized_target = self._normalize_model_name(model)
        for candidate in local_models:
            if self._normalize_model_name(candidate) == normalized_target:
                return candidate
        for candidate in local_models:
            if normalized_target and normalized_target in self._normalize_model_name(candidate):
                return candidate
        return model

    def list_running_models(self) -> list[str]:
        with self._client() as client:
            resp = client.get(f"{self.base_url}/api/ps")
            resp.raise_for_status()
            data = resp.json()
            models = data.get("models", [])
            result: list[str] = []
            for m in models:
                name = m.get("name")
                if name:
                    result.append(name)
            return result

    def stop_model(self, model: str) -> None:
        # keep_alive=0 unloads model from memory
        with self._client() as client:
            client.post(
                f"{self.base_url}/api/generate",
                json={"model": model, "prompt": "", "stream": False, "keep_alive": 0},
            )

    def activate_model(self, model: str) -> dict:
        resolved_model = self.resolve_model_name(model)
        running = self.list_running_models()
        for m in running:
            if m != resolved_model:
                self.stop_model(m)
        # Warm up target model; for embedding-only models, fallback to /api/embeddings.
        with self._client() as client:
            try:
                resp = client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": resolved_model,
                        "prompt": "ping",
                        "stream": False,
                        "keep_alive": "10m",
                    },
                )
                resp.raise_for_status()
            except httpx.HTTPStatusError:
                emb_resp = client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": resolved_model, "prompt": "ping"},
                )
                emb_resp.raise_for_status()
        return {
            "requested_model": model,
            "active_model": resolved_model,
            "stopped_models": [m for m in running if m != resolved_model],
        }
