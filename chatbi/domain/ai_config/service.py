from __future__ import annotations

import os
import uuid
import base64
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import duckdb
import httpx
import pandas as pd
from openai import OpenAI
from qdrant_client.models import FieldCondition, Filter, MatchValue, PointStruct

from chatbi.database.qdrant import get_qdrant_manager
from chatbi.domain.datasource import DataSourceCreate, DatabaseType
from chatbi.domain.datasource.repository import DatasourceRepository
from chatbi.domain.datasource.service import DatasourceService
from chatbi.domain.ai_config.dtos import (
    LLMSourceCreateDTO,
    LLMSourceUpdateDTO,
    RagDocumentDTO,
)
from chatbi.domain.ai_config.models import SceneType
from chatbi.domain.ai_config.repository import AIConfigRepository
from chatbi.domain.ai_config.runtime import OllamaRuntimeManager


class AIConfigService:
    def __init__(self, repo: Optional[AIConfigRepository] = None) -> None:
        self.repo = repo or AIConfigRepository()
        self.runtime = OllamaRuntimeManager(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        )

    def list_llm_sources(self) -> list[dict[str, Any]]:
        return self.repo.read_config()["llm_sources"]

    def create_llm_source(self, payload: LLMSourceCreateDTO) -> dict[str, Any]:
        cfg = self.repo.read_config()
        sources = cfg["llm_sources"]
        now = datetime.utcnow().isoformat()
        item = {
            "id": os.urandom(8).hex(),
            "name": payload.name,
            "provider": payload.provider,
            "base_url": payload.base_url,
            "model": payload.model,
            "api_key": payload.api_key,
            "description": payload.description,
            "is_default": payload.is_default,
            "enabled": payload.enabled,
            "capability": payload.capability,
            "created_at": now,
            "updated_at": now,
        }
        if payload.is_default:
            for src in sources:
                src["is_default"] = False
        sources.append(item)
        self.repo.write_config(cfg)
        return item

    def update_llm_source(self, llm_source_id: str, payload: LLMSourceUpdateDTO) -> dict[str, Any]:
        cfg = self.repo.read_config()
        sources = cfg["llm_sources"]
        for src in sources:
            if src["id"] != llm_source_id:
                continue
            data = payload.model_dump(exclude_unset=True)
            src.update(data)
            src["updated_at"] = datetime.utcnow().isoformat()
            if src.get("is_default"):
                for other in sources:
                    if other["id"] != src["id"]:
                        other["is_default"] = False
            self.repo.write_config(cfg)
            return src
        raise ValueError(f"LLM source not found: {llm_source_id}")

    def delete_llm_source(self, llm_source_id: str) -> None:
        cfg = self.repo.read_config()
        before = len(cfg["llm_sources"])
        cfg["llm_sources"] = [x for x in cfg["llm_sources"] if x["id"] != llm_source_id]
        if len(cfg["llm_sources"]) == before:
            raise ValueError(f"LLM source not found: {llm_source_id}")
        if not any(x.get("is_default") for x in cfg["llm_sources"]) and cfg["llm_sources"]:
            cfg["llm_sources"][0]["is_default"] = True
        for scene, binding in list(cfg["scene_llm_binding"].items()):
            if binding == llm_source_id:
                cfg["scene_llm_binding"][scene] = self._get_default_source_id(cfg)
        self.repo.write_config(cfg)

    def _get_default_source_id(self, cfg: dict[str, Any]) -> Optional[str]:
        for src in cfg["llm_sources"]:
            if src.get("is_default"):
                return src["id"]
        return cfg["llm_sources"][0]["id"] if cfg["llm_sources"] else None

    def get_scene_prompt(self, scene: SceneType | str) -> str:
        scene_val = scene.value if isinstance(scene, SceneType) else scene
        cfg = self.repo.read_config()
        return cfg["scene_prompts"].get(scene_val, "")

    def set_scene_prompt(self, scene: SceneType | str, prompt: str) -> dict[str, str]:
        scene_val = scene.value if isinstance(scene, SceneType) else scene
        cfg = self.repo.read_config()
        cfg["scene_prompts"][scene_val] = prompt
        self.repo.write_config(cfg)
        return {"scene": scene_val, "prompt": prompt}

    def list_scene_prompts(self) -> dict[str, str]:
        cfg = self.repo.read_config()
        return cfg["scene_prompts"]

    def bind_scene_llm(self, scene: SceneType | str, llm_source_id: str) -> dict[str, str]:
        scene_val = scene.value if isinstance(scene, SceneType) else scene
        cfg = self.repo.read_config()
        if not any(x["id"] == llm_source_id for x in cfg["llm_sources"]):
            raise ValueError(f"LLM source not found: {llm_source_id}")
        cfg["scene_llm_binding"][scene_val] = llm_source_id
        self.repo.write_config(cfg)
        return {"scene": scene_val, "llm_source_id": llm_source_id}

    def resolve_llm_source(self, scene: SceneType | str, llm_source_id: Optional[str] = None) -> Optional[dict[str, Any]]:
        cfg = self.repo.read_config()
        scene_val = scene.value if isinstance(scene, SceneType) else scene
        sources = [x for x in cfg["llm_sources"] if x.get("enabled", True)]
        if not sources:
            return None
        target_id = llm_source_id or cfg["scene_llm_binding"].get(scene_val) or self._get_default_source_id(cfg)
        for src in sources:
            if src["id"] == target_id:
                resolved = dict(src)
                if resolved.get("model"):
                    resolved["model"] = self.runtime.resolve_model_name(str(resolved["model"]))
                return resolved
        fallback = dict(sources[0])
        if fallback.get("model"):
            fallback["model"] = self.runtime.resolve_model_name(str(fallback["model"]))
        return fallback

    def get_model_capabilities(self) -> dict[str, str]:
        cfg = self.repo.read_config()
        return cfg.get("model_capabilities", {})

    def set_model_capability(self, capability: str, model: str) -> dict[str, str]:
        cfg = self.repo.read_config()
        caps = cfg.setdefault("model_capabilities", {})
        resolved = self.runtime.resolve_model_name(model)
        caps[capability] = resolved
        self.repo.write_config(cfg)
        return {"capability": capability, "model": resolved}

    def activate_capability_model(self, capability: str) -> dict[str, Any]:
        caps = self.get_model_capabilities()
        model = caps.get(capability)
        if not model:
            raise ValueError(f"Capability model not configured: {capability}")
        result = self.runtime.activate_model(model)
        cfg = self.repo.read_config()
        cfg["active_runtime_model"] = result.get("active_model", model)
        self.repo.write_config(cfg)
        return {"capability": capability, **result}

    def activate_specific_model(self, model: str) -> dict[str, Any]:
        result = self.runtime.activate_model(model)
        cfg = self.repo.read_config()
        cfg["active_runtime_model"] = result.get("active_model", model)
        self.repo.write_config(cfg)
        return result

    def get_runtime_status(self) -> dict[str, Any]:
        cfg = self.repo.read_config()
        return {
            "active_runtime_model": cfg.get("active_runtime_model"),
            "running_models": self.runtime.list_running_models(),
            "local_models": self.runtime.list_local_models(),
            "model_capabilities": cfg.get("model_capabilities", {}),
        }

    def list_rag_documents(self) -> list[RagDocumentDTO]:
        docs: list[RagDocumentDTO] = []
        for p in self.repo.list_rag_files():
            st = p.stat()
            docs.append(
                RagDocumentDTO(
                    id=p.name,
                    filename=p.name,
                    path=str(p),
                    size=st.st_size,
                    updated_at=datetime.fromtimestamp(st.st_mtime),
                )
            )
        return docs

    def save_rag_document(self, filename: str, content: bytes) -> RagDocumentDTO:
        path = self.repo.rag_path(filename)
        path.write_bytes(content)
        self.sync_document_to_qdrant(path)
        st = path.stat()
        return RagDocumentDTO(
            id=path.name,
            filename=path.name,
            path=str(path),
            size=st.st_size,
            updated_at=datetime.fromtimestamp(st.st_mtime),
        )

    def delete_rag_document(self, filename: str) -> None:
        path = self.repo.rag_path(filename)
        if not path.exists():
            raise ValueError(f"File not found: {filename}")
        path.unlink()
        manager = get_qdrant_manager()
        manager.delete_points_by_filter(
            collection_name="smartbi_rag_knowledge",
            filter_conditions=Filter(
                must=[
                    FieldCondition(
                        key="filename",
                        match=MatchValue(value=filename),
                    )
                ]
            ),
        )

    def list_datasource_presets(self) -> dict[str, Any]:
        root = Path(os.getcwd())
        files: list[dict[str, Any]] = []
        for folder_name in ["data", "Data"]:
            folder = root / folder_name
            if not folder.exists():
                continue
            for f in folder.glob("*"):
                if f.suffix.lower() not in {".xlsx", ".xls", ".csv"}:
                    continue
                files.append(
                    {
                        "name": f.name,
                        "path": str(f),
                        "type": "excel" if f.suffix.lower() in {".xlsx", ".xls"} else "csv",
                        "size": f.stat().st_size,
                    }
                )

        mysql_preset = {
            "type": "mysql",
            "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
            "port": os.getenv("MYSQL_PORT", "3306"),
            "database": os.getenv("MYSQL_DB", "loan_analytics"),
            "username": os.getenv("MYSQL_USER", "root"),
        }
        return {"local_files": files, "mysql": mysql_preset}

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 600, overlap: int = 100) -> list[str]:
        chunks: list[str] = []
        i = 0
        while i < len(text):
            chunks.append(text[i : i + chunk_size])
            i += max(1, chunk_size - overlap)
        return [c.strip() for c in chunks if c.strip()]

    @staticmethod
    def _embed_text_ollama(text: str) -> list[float]:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        model = os.getenv("OLLAMA_EMBED_MODEL", "bge-m3")
        resp = httpx.post(
            f"{base_url}/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        embedding = data.get("embedding")
        if not embedding or not isinstance(embedding, list):
            raise RuntimeError("Invalid embedding response from Ollama")
        return [float(v) for v in embedding]

    def sync_document_to_qdrant(self, path: Path) -> int:
        embed_model = self.get_model_capabilities().get("embedding", "bge-m3")
        os.environ["OLLAMA_EMBED_MODEL"] = self.runtime.resolve_model_name(embed_model)
        self.activate_capability_model("embedding")
        raw = path.read_text(encoding="utf-8", errors="ignore")
        chunks = self._chunk_text(raw)
        if not chunks:
            return 0

        manager = get_qdrant_manager()
        first_embedding = self._embed_text_ollama(chunks[0])
        dim = len(first_embedding)
        collection_name = "smartbi_rag_knowledge"

        # Ensure vector size matches embedding model dimension
        collections = manager.client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)
        if exists:
            info = manager.client.get_collection(collection_name)
            current_dim = info.config.params.vectors.size
            if current_dim != dim:
                manager.delete_collection(collection_name)
                exists = False
        if not exists:
            manager.create_collection_if_not_exists(
                collection_name=collection_name,
                vector_size=dim,
            )

        points: list[PointStruct] = []
        for i, chunk in enumerate(chunks):
            embedding = first_embedding if i == 0 else self._embed_text_ollama(chunk)
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "filename": path.name,
                        "chunk_index": i,
                        "text": chunk,
                        "source": str(path),
                        "embedding_model": os.getenv("OLLAMA_EMBED_MODEL", "bge-m3"),
                    },
                )
            )
        if points:
            manager.upsert_points(collection_name=collection_name, points=points)
        return len(points)

    def sync_all_rag_to_qdrant(self) -> dict[str, int]:
        result: dict[str, int] = {}
        for p in self.repo.list_rag_files():
            result[p.name] = self.sync_document_to_qdrant(p)
        return result

    def retrieve_rag_context(self, query: str, top_k: int = 4) -> str:
        try:
            embed_model = self.get_model_capabilities().get("embedding", "bge-m3")
            os.environ["OLLAMA_EMBED_MODEL"] = self.runtime.resolve_model_name(embed_model)
            self.activate_capability_model("embedding")
            manager = get_qdrant_manager()
            query_embedding = self._embed_text_ollama(query)
            hits = manager.search(
                collection_name="smartbi_rag_knowledge",
                query_vector=query_embedding,
                limit=top_k,
            )
            texts = []
            for h in hits:
                payload = h.get("payload") or {}
                text = payload.get("text")
                filename = payload.get("filename", "unknown")
                if text:
                    texts.append(f"[{filename}] {text}")
            return "\n".join(texts)
        except Exception:
            return ""

    def analyze_image_with_vision_model(self, image_bytes: bytes, prompt: str) -> dict[str, Any]:
        caps = self.get_model_capabilities()
        model = caps.get("vision", "minicpm-v4")
        self.activate_capability_model("vision")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        client = OpenAI(base_url=f"{base_url}/v1", api_key="ollama")
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                    ],
                }
            ],
            temperature=0.2,
        )
        content = resp.choices[0].message.content if resp.choices else ""
        return {"model": model, "answer": content}

    def analyze_table_with_table_model(self, table_text: str, prompt: str) -> dict[str, Any]:
        caps = self.get_model_capabilities()
        model = caps.get("table", "TableGPT2-7B")
        self.activate_capability_model("table")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        client = OpenAI(base_url=f"{base_url}/v1", api_key="ollama")
        full_prompt = (
            "你是表格分析专家。请针对下方表格数据回答，输出关键结论、异常点和建议。\n\n"
            f"[问题]\n{prompt}\n\n[表格数据]\n{table_text}"
        )
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.2,
        )
        content = resp.choices[0].message.content if resp.choices else ""
        return {"model": model, "answer": content}

    async def quick_create_mysql_datasource(
        self,
        repo: DatasourceRepository,
        datasource_name: str = "Local MySQL (Quick Create)",
    ) -> dict[str, Any]:
        try:
            service = DatasourceService(repo=repo)
            existed = await repo.get_by_name(datasource_name)
            if existed:
                return {"id": str(existed.id), "name": existed.name, "type": existed.type}
            payload = DataSourceCreate(
                name=datasource_name,
                description="Auto-created from SmartBI quick setup",
                type=DatabaseType.MYSQL,
                connection_info={
                    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
                    "port": os.getenv("MYSQL_PORT", "3306"),
                    "database": os.getenv("MYSQL_DB", "loan_analytics"),
                    "user": os.getenv("MYSQL_USER", "root"),
                    "password": os.getenv("MYSQL_PASSWORD", "root"),
                },
            )
            ds = await service.create_datasource(payload)
            return {"id": str(ds.id), "name": ds.name, "type": ds.type}
        except Exception as e:
            return {
                "id": f"tmp-{uuid.uuid4()}",
                "name": datasource_name,
                "type": DatabaseType.MYSQL.value,
                "warning": f"Created config in memory only, metadata DB unavailable: {e}",
            }

    async def quick_create_excel_datasource(
        self,
        repo: DatasourceRepository,
        datasource_name: str = "Local Excel Mart (Quick Create)",
    ) -> dict[str, Any]:
        presets = self.list_datasource_presets()
        files = presets.get("local_files", [])

        duckdb_path = Path(os.getcwd()) / "runs" / "local_excel_mart.duckdb"
        conn = duckdb.connect(str(duckdb_path))
        try:
            for f in files:
                table_name = Path(f["name"]).stem.replace("-", "_").replace(" ", "_")
                file_path = f["path"]
                if f["type"] == "csv":
                    conn.execute(
                        f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv_auto('{file_path}')"
                    )
                else:
                    df = pd.read_excel(file_path)
                    conn.register("tmp_df", df)
                    conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM tmp_df")
                    conn.unregister("tmp_df")
            conn.execute(
                """
                CREATE OR REPLACE TABLE loan_fact_daily AS
                WITH d AS (
                  SELECT
                    CAST(CURRENT_DATE - INTERVAL '180 days' AS DATE) + CAST(i AS INTEGER) AS biz_date,
                    CASE WHEN i % 2 = 0 THEN 'business' ELSE 'consumer' END AS loan_type,
                    0.45 + (i % 10) * 0.02 AS final_approval_rate,
                    0.35 + (i % 8) * 0.03 AS credit_utilization_rate,
                    0.01 + (i % 6) * 0.005 AS overdue_rate,
                    0.02 + (i % 5) * 0.004 AS migration_rate_m1_to_m3,
                    0.08 + (i % 7) * 0.01 AS raroc,
                    0.05 + (i % 6) * 0.008 AS net_interest_margin,
                    0.22 + (i % 4) * 0.02 AS cost_income_ratio,
                    0.012 + (i % 5) * 0.002 AS npl_ratio,
                    2.0 + (i % 5) * 0.2 AS provision_coverage,
                    0.12 + (i % 6) * 0.01 AS capital_adequacy_ratio
                  FROM range(180) t(i)
                )
                SELECT * FROM d
                """
            )
            conn.execute(
                """
                CREATE OR REPLACE TABLE loan_funnel_daily AS
                WITH d AS (
                  SELECT
                    CAST(CURRENT_DATE - INTERVAL '180 days' AS DATE) + CAST(i AS INTEGER) AS biz_date,
                    CASE WHEN i % 2 = 0 THEN 'business' ELSE 'consumer' END AS loan_type,
                    CASE WHEN i % 3 = 0 THEN '线上' WHEN i % 3 = 1 THEN '线下' ELSE '联合贷' END AS channel,
                    CASE WHEN i % 3 = 0 THEN 'A客群' WHEN i % 3 = 1 THEN 'B客群' ELSE 'C客群' END AS customer_segment,
                    CASE WHEN i % 2 = 0 THEN '新客' ELSE '老客' END AS customer_group,
                    (i % 50) + 1000 AS bdm_id,
                    1 AS bdm_active,
                    0.4 + (i % 8) * 0.03 AS channel_pass_rate,
                    20 + (i % 15) AS register_user_cnt,
                    18 + (i % 12) AS apply_order_cnt,
                    0.6 + (i % 10) * 0.02 AS completion_rate,
                    8 + (i % 6) AS stage1_enter_user_cnt,
                    6 + (i % 5) AS stage1_pass_user_cnt,
                    5 + (i % 4) AS stage1_success_order_cnt,
                    5 + (i % 4) AS stage2_enter_user_cnt,
                    4 + (i % 3) AS stage2_pass_user_cnt,
                    3 + (i % 3) AS stage2_success_user_cnt,
                    3 + (i % 3) AS stage3_enter_user_cnt,
                    2 + (i % 2) AS stage3_success_user_cnt,
                    10 + (i % 6) AS disburse_user_t30_cnt,
                    14 + (i % 8) AS disburse_order_cnt,
                    (120000 + i * 1100) * 1.0 AS disburse_amount,
                    120 + (i % 18) AS onbook_user_cnt,
                    9 + (i % 5) AS new_onbook_user_cnt,
                    7 + (i % 4) AS repaid_user_cnt,
                    4 + (i % 3) AS overdue_user_cnt,
                    0.01 + (i % 6) * 0.004 AS overdue_rate,
                    0.008 + (i % 5) * 0.003 AS npl_ratio,
                    0.018 + (i % 5) * 0.004 AS migration_rate_m1_to_m3,
                    0.08 + (i % 7) * 0.01 AS raroc,
                    0.05 + (i % 6) * 0.008 AS net_interest_margin,
                    0.20 + (i % 5) * 0.02 AS cost_income_ratio,
                    1.8 + (i % 4) * 0.3 AS provision_coverage,
                    0.11 + (i % 6) * 0.01 AS capital_adequacy_ratio,
                    5 + (i % 4) AS facecheck_need_user_cnt,
                    4 + (i % 3) AS facecheck_pass_user_cnt,
                    4 + (i % 3) AS phonecheck_pass_user_cnt,
                    6 + (i % 4) AS final_pass_user_cnt,
                    6 + (i % 4) AS final_pass_order_cnt
                  FROM range(180) t(i)
                )
                SELECT * FROM d
                """
            )
        finally:
            conn.close()

        try:
            service = DatasourceService(repo=repo)
            existed = await repo.get_by_name(datasource_name)
            if existed:
                return {
                    "id": str(existed.id),
                    "name": existed.name,
                    "type": existed.type,
                    "path": str(duckdb_path),
                }
            payload = DataSourceCreate(
                name=datasource_name,
                description="Auto-created DuckDB mart from local excel/csv files",
                type=DatabaseType.DUCKDB,
                connection_info={"path": str(duckdb_path)},
            )
            ds = await service.create_datasource(payload)
            return {"id": str(ds.id), "name": ds.name, "type": ds.type, "path": str(duckdb_path)}
        except Exception as e:
            return {
                "id": f"tmp-{uuid.uuid4()}",
                "name": datasource_name,
                "type": DatabaseType.DUCKDB.value,
                "path": str(duckdb_path),
                "warning": f"Mart created but metadata DB unavailable: {e}",
            }
