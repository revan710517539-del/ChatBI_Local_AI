"""
MDL API Router

REST endpoints for MDL management:
- GET /api/v1/mdl/projects - List projects
- POST /api/v1/mdl/projects - Create project
- GET /api/v1/mdl/projects/{id} - Get project detail
- PUT /api/v1/mdl/projects/{id} - Update project
- DELETE /api/v1/mdl/projects/{id} - Delete project
- GET /api/v1/mdl/projects/{id}/models - List models
- POST /api/v1/mdl/projects/{id}/models - Create model
- GET /api/v1/mdl/models/{id} - Get model detail
- PUT /api/v1/mdl/models/{id} - Update model
- DELETE /api/v1/mdl/models/{id} - Delete model
- POST /api/v1/mdl/sync - Trigger MDL indexing from Cube.js
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from loguru import logger

from chatbi.agent.llm.openai import OpenaiModel
from chatbi.dependencies import (
    AsyncQdrantDep,
    get_current_user,
    RepositoryDependency,
)
from chatbi.domain.auth.models import User
from chatbi.domain.mdl.dtos import (
    CreateMDLModelDTO,
    CreateMDLProjectDTO,
    MDLModelDetailDTO,
    MDLProjectDetailDTO,
    MDLSyncRequestDTO,
    MDLSyncResponseDTO,
    UpdateMDLModelDTO,
    UpdateMDLProjectDTO,
)
from chatbi.domain.mdl.repository import (
    AsyncMDLModelRepository,
    AsyncMDLProjectRepository,
)
from chatbi.domain.mdl.service import MDLService

router = APIRouter(prefix="/api/v1/mdl", tags=["MDL"])

# Dependency factories
MDLProjectRepoDep = RepositoryDependency(AsyncMDLProjectRepository)
MDLModelRepoDep = RepositoryDependency(AsyncMDLModelRepository)


def get_mdl_service(
    project_repo: AsyncMDLProjectRepository = Depends(MDLProjectRepoDep),
    model_repo: AsyncMDLModelRepository = Depends(MDLModelRepoDep),
) -> MDLService:
    """Create MDL service with injected repositories"""
    return MDLService(project_repo, model_repo)


# ===== Project Endpoints =====


@router.get("/projects", response_model=List[MDLProjectDetailDTO])
async def list_projects(
    datasource_id: Optional[UUID] = Query(None, description="Filter by datasource ID"),
    skip: int = Query(0, ge=0, description="Skip N records"),
    limit: int = Query(100, ge=1, le=1000, description="Limit results"),
    service: MDLService = Depends(get_mdl_service),
    user: User = Depends(get_current_user),
):
    """List MDL projects"""
    logger.info(
        f"Listing MDL projects for user {user.user_id} (datasource_id={datasource_id})"
    )
    projects = await service.list_projects(
        datasource_id=datasource_id,
        owner_id=None,  # TODO: Filter by user.user_id if not admin
        skip=skip,
        limit=limit,
    )
    return projects


@router.post("/projects", response_model=MDLProjectDetailDTO, status_code=201)
async def create_project(
    dto: CreateMDLProjectDTO,
    service: MDLService = Depends(get_mdl_service),
    user: User = Depends(get_current_user),
):
    """Create a new MDL project"""
    logger.info(f"Creating MDL project: {dto.name} for user {user.user_id}")
    project = await service.create_project(dto, owner_id=user.user_id)
    return project


@router.get("/projects/{project_id}", response_model=MDLProjectDetailDTO)
async def get_project(
    project_id: UUID,
    service: MDLService = Depends(get_mdl_service),
    user: User = Depends(get_current_user),
):
    """Get MDL project by ID"""
    logger.info(f"Getting MDL project: {project_id}")
    project = await service.get_project(project_id)
    if not project:
        from chatbi.exceptions import NotFoundError

        raise NotFoundError(f"MDL project not found: {project_id}")
    return project


@router.put("/projects/{project_id}", response_model=MDLProjectDetailDTO)
async def update_project(
    project_id: UUID,
    dto: UpdateMDLProjectDTO,
    service: MDLService = Depends(get_mdl_service),
    user: User = Depends(get_current_user),
):
    """Update an MDL project"""
    logger.info(f"Updating MDL project: {project_id}")
    project = await service.update_project(project_id, dto)
    return project


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(
    project_id: UUID,
    service: MDLService = Depends(get_mdl_service),
    user: User = Depends(get_current_user),
):
    """Delete an MDL project"""
    logger.info(f"Deleting MDL project: {project_id}")
    await service.delete_project(project_id)


# ===== Model Endpoints =====


@router.get("/projects/{project_id}/models", response_model=List[MDLModelDetailDTO])
async def list_models(
    project_id: UUID,
    service: MDLService = Depends(get_mdl_service),
    user: User = Depends(get_current_user),
):
    """List models in a project"""
    logger.info(f"Listing MDL models for project: {project_id}")
    models = await service.list_models(project_id)
    return models


@router.post(
    "/projects/{project_id}/models", response_model=MDLModelDetailDTO, status_code=201
)
async def create_model(
    project_id: UUID,
    dto: CreateMDLModelDTO,
    service: MDLService = Depends(get_mdl_service),
    user: User = Depends(get_current_user),
):
    """Create a new MDL model"""
    logger.info(f"Creating MDL model: {dto.name} in project {project_id}")
    model = await service.create_model(project_id, dto)
    return model


@router.get("/models/{model_id}", response_model=MDLModelDetailDTO)
async def get_model(
    model_id: UUID,
    service: MDLService = Depends(get_mdl_service),
    user: User = Depends(get_current_user),
):
    """Get MDL model by ID"""
    logger.info(f"Getting MDL model: {model_id}")
    model = await service.get_model(model_id)
    if not model:
        from chatbi.exceptions import NotFoundError

        raise NotFoundError(f"MDL model not found: {model_id}")
    return model


@router.put("/models/{model_id}", response_model=MDLModelDetailDTO)
async def update_model(
    model_id: UUID,
    dto: UpdateMDLModelDTO,
    service: MDLService = Depends(get_mdl_service),
    user: User = Depends(get_current_user),
):
    """Update an MDL model"""
    logger.info(f"Updating MDL model: {model_id}")
    model = await service.update_model(model_id, dto)
    return model


@router.delete("/models/{model_id}", status_code=204)
async def delete_model(
    model_id: UUID,
    service: MDLService = Depends(get_mdl_service),
    user: User = Depends(get_current_user),
):
    """Delete an MDL model"""
    logger.info(f"Deleting MDL model: {model_id}")
    await service.delete_model(model_id)


# ===== MDL Sync Endpoint =====


@router.post("/sync", response_model=MDLSyncResponseDTO)
async def sync_mdl(
    dto: MDLSyncRequestDTO,
    qdrant: AsyncQdrantDep,
    user: User = Depends(get_current_user),
):
    """
    Trigger MDL indexing from Cube.js metadata
    
    This endpoint:
    1. Fetches metadata from Cube.js API
    2. Transforms cubes to MDL models
    3. Generates embeddings
    4. Stores in Qdrant for semantic search
    
    Args:
        dto: Sync request with project_id, datasource_id, force_refresh
        qdrant: Qdrant manager dependency
        user: Current authenticated user
    
    Returns:
        MDLSyncResponseDTO with sync status and statistics
    """
    logger.info(
        f"Triggering MDL sync for project {dto.project_id}, datasource {dto.datasource_id} (force_refresh={dto.force_refresh})"
    )

    # Initialize LLM provider for embeddings
    llm_provider = OpenaiModel()

    # Cube.js removed - sync disabled
    # Return dummy success
    return MDLSyncResponseDTO(
        status="skipped",
        models_count=0,
        indexed_documents=0,
        elapsed_time_ms=0,
        error="Cube.js integration removed",
    )
