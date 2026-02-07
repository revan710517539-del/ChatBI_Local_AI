from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from chatbi.dependencies import RepositoryDependency, transactional
from chatbi.domain.datasource.repository import DatasourceRepository
from chatbi.domain.ai_config.dtos import (
    CapabilityModelUpdateDTO,
    LLMSourceCreateDTO,
    LLMSourceUpdateDTO,
    PromptUpdateDTO,
    SceneModelBindingDTO,
    TableAnalyzeDTO,
)
from chatbi.domain.ai_config.service import AIConfigService
from chatbi.middleware.standard_response import StandardResponse

router = APIRouter(prefix="/api/v1/ai-config", tags=["AI Config"])
DatasourceRepoDep = RepositoryDependency(DatasourceRepository)


@router.get("/llm-sources")
async def list_llm_sources():
    service = AIConfigService()
    return StandardResponse(
        status="success",
        message="LLM sources fetched",
        data=service.list_llm_sources(),
    )


@router.post("/llm-sources")
async def create_llm_source(payload: LLMSourceCreateDTO):
    service = AIConfigService()
    return StandardResponse(
        status="success",
        message="LLM source created",
        data=service.create_llm_source(payload),
    )


@router.put("/llm-sources/{llm_source_id}")
async def update_llm_source(llm_source_id: str, payload: LLMSourceUpdateDTO):
    service = AIConfigService()
    return StandardResponse(
        status="success",
        message="LLM source updated",
        data=service.update_llm_source(llm_source_id, payload),
    )


@router.delete("/llm-sources/{llm_source_id}")
async def delete_llm_source(llm_source_id: str):
    service = AIConfigService()
    service.delete_llm_source(llm_source_id)
    return StandardResponse(
        status="success",
        message="LLM source deleted",
        data={"id": llm_source_id},
    )


@router.get("/prompts")
async def list_prompts():
    service = AIConfigService()
    return StandardResponse(
        status="success",
        message="Prompts fetched",
        data=service.list_scene_prompts(),
    )


@router.put("/prompts")
async def update_prompt(payload: PromptUpdateDTO):
    service = AIConfigService()
    return StandardResponse(
        status="success",
        message="Prompt updated",
        data=service.set_scene_prompt(payload.scene, payload.prompt),
    )


@router.put("/scene-llm-binding")
async def bind_scene_model(payload: SceneModelBindingDTO):
    service = AIConfigService()
    return StandardResponse(
        status="success",
        message="Scene model binding updated",
        data=service.bind_scene_llm(payload.scene, payload.llm_source_id),
    )


@router.get("/scene-llm-binding")
async def get_scene_model_binding():
    service = AIConfigService()
    cfg = service.repo.read_config()
    return StandardResponse(
        status="success",
        message="Scene model binding fetched",
        data=cfg.get("scene_llm_binding", {}),
    )


@router.get("/rag/documents")
async def list_rag_documents():
    service = AIConfigService()
    return StandardResponse(
        status="success",
        message="RAG documents fetched",
        data=[d.model_dump() for d in service.list_rag_documents()],
    )


@router.post("/rag/documents")
async def upload_rag_document(file: UploadFile = File(...)):
    service = AIConfigService()
    content = await file.read()
    doc = service.save_rag_document(file.filename, content)
    return StandardResponse(
        status="success",
        message="RAG document uploaded",
        data=doc.model_dump(),
    )


@router.post("/rag/sync")
async def sync_rag_vector_store():
    service = AIConfigService()
    result = service.sync_all_rag_to_qdrant()
    return StandardResponse(
        status="success",
        message="RAG vector index synced",
        data=result,
    )


@router.delete("/rag/documents/{filename}")
async def delete_rag_document(filename: str):
    service = AIConfigService()
    service.delete_rag_document(filename)
    return StandardResponse(
        status="success",
        message="RAG document deleted",
        data={"filename": filename},
    )


@router.get("/datasource-presets")
async def list_datasource_presets():
    service = AIConfigService()
    return StandardResponse(
        status="success",
        message="Datasource presets fetched",
        data=service.list_datasource_presets(),
    )


@router.get("/runtime/status")
async def runtime_status():
    service = AIConfigService()
    return StandardResponse(
        status="success",
        message="Runtime status fetched",
        data=service.get_runtime_status(),
    )


@router.post("/runtime/activate/{capability}")
async def activate_runtime_model(capability: str):
    service = AIConfigService()
    return StandardResponse(
        status="success",
        message="Runtime model activated",
        data=service.activate_capability_model(capability),
    )


@router.get("/runtime/capabilities")
async def get_runtime_capabilities():
    service = AIConfigService()
    return StandardResponse(
        status="success",
        message="Capability models fetched",
        data=service.get_model_capabilities(),
    )


@router.put("/runtime/capabilities")
async def update_runtime_capability(payload: CapabilityModelUpdateDTO):
    service = AIConfigService()
    return StandardResponse(
        status="success",
        message="Capability model updated",
        data=service.set_model_capability(payload.capability, payload.model),
    )


@router.post("/vision/analyze")
async def analyze_vision(
    prompt: str = Form(...),
    image: UploadFile = File(...),
):
    service = AIConfigService()
    content = await image.read()
    data = service.analyze_image_with_vision_model(content, prompt)
    return StandardResponse(
        status="success",
        message="Vision analysis completed",
        data=data,
    )


@router.post("/table/analyze")
async def analyze_table(payload: TableAnalyzeDTO):
    service = AIConfigService()
    data = service.analyze_table_with_table_model(
        table_text=payload.table_text,
        prompt=payload.prompt,
    )
    return StandardResponse(
        status="success",
        message="Table analysis completed",
        data=data,
    )


@router.post("/datasource/quick-create/mysql")
@transactional
async def quick_create_mysql(
    repo: DatasourceRepository = Depends(DatasourceRepoDep),
):
    service = AIConfigService()
    created = await service.quick_create_mysql_datasource(repo=repo)
    return StandardResponse(
        status="success",
        message="MySQL datasource created",
        data=created,
    )


@router.post("/datasource/quick-create/excel")
@transactional
async def quick_create_excel(
    repo: DatasourceRepository = Depends(DatasourceRepoDep),
):
    service = AIConfigService()
    created = await service.quick_create_excel_datasource(repo=repo)
    return StandardResponse(
        status="success",
        message="Excel datasource created",
        data=created,
    )
