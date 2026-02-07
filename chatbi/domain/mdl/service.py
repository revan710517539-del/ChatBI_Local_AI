"""
MDL Service Layer

Business logic for MDL operations:
- Project management (CRUD)
- Model management (CRUD)
- MDL synchronization (Cube.js metadata → MDL)
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from loguru import logger

from chatbi.domain.mdl.dtos import (
    CreateMDLModelDTO,
    CreateMDLProjectDTO,
    MDLModelDetailDTO,
    MDLProjectDetailDTO,
    UpdateMDLModelDTO,
    UpdateMDLProjectDTO,
)
from chatbi.domain.mdl.models import MDLColumn, MDLMetric, MDLModel, MDLProject
from chatbi.domain.mdl.repository import (
    AsyncMDLModelRepository,
    AsyncMDLProjectRepository,
)
from chatbi.exceptions import NotFoundError, ValidationError


class MDLService:
    """MDL domain service"""

    def __init__(
        self,
        project_repo: AsyncMDLProjectRepository,
        model_repo: AsyncMDLModelRepository,
    ):
        self.project_repo = project_repo
        self.model_repo = model_repo

    # ===== Project Operations =====

    async def get_project(self, project_id: UUID) -> Optional[MDLProjectDetailDTO]:
        """Get project by ID"""
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            return None

        return MDLProjectDetailDTO(
            id=project.id,
            name=project.name,
            description=project.description,
            datasource_id=project.datasource_id,
            owner_id=project.owner_id,
            models=project.models,
            metrics=project.metrics,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    async def list_projects(
        self,
        datasource_id: Optional[UUID] = None,
        owner_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MDLProjectDetailDTO]:
        """List projects with optional filters"""
        if datasource_id:
            projects = await self.project_repo.get_by_datasource(datasource_id)
        elif owner_id:
            projects = await self.project_repo.get_by_owner(owner_id)
        else:
            projects = await self.project_repo.get_all(skip=skip, limit=limit)

        return [
            MDLProjectDetailDTO(
                id=p.id,
                name=p.name,
                description=p.description,
                datasource_id=p.datasource_id,
                owner_id=p.owner_id,
                models=p.models,
                metrics=p.metrics,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in projects
        ]

    async def create_project(
        self, dto: CreateMDLProjectDTO, owner_id: UUID
    ) -> MDLProjectDetailDTO:
        """Create a new MDL project"""
        now = datetime.utcnow()
        project = MDLProject(
            id=uuid4(),
            name=dto.name,
            description=dto.description,
            datasource_id=dto.datasource_id,
            owner_id=owner_id,
            models=[],
            metrics=[],
            created_at=now,
            updated_at=now,
        )

        created = await self.project_repo.create(project)
        logger.info(f"Created MDL project: {created.id}")

        return MDLProjectDetailDTO(
            id=created.id,
            name=created.name,
            description=created.description,
            datasource_id=created.datasource_id,
            owner_id=created.owner_id,
            models=created.models,
            metrics=created.metrics,
            created_at=created.created_at,
            updated_at=created.updated_at,
        )

    async def update_project(
        self, project_id: UUID, dto: UpdateMDLProjectDTO
    ) -> MDLProjectDetailDTO:
        """Update an MDL project"""
        update_data = dto.model_dump(exclude_unset=True)

        # Handle metrics separately if provided
        if "metrics" in update_data:
            metrics = update_data.pop("metrics")
            # Store in metadata field
            update_data["metadata"] = {"metrics": [m.model_dump() for m in metrics]}

        updated = await self.project_repo.update(project_id, **update_data)
        if not updated:
            raise NotFoundError(f"MDL project not found: {project_id}")

        logger.info(f"Updated MDL project: {project_id}")
        return MDLProjectDetailDTO(
            id=updated.id,
            name=updated.name,
            description=updated.description,
            datasource_id=updated.datasource_id,
            owner_id=updated.owner_id,
            models=updated.models,
            metrics=updated.metrics,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )

    async def delete_project(self, project_id: UUID) -> bool:
        """Delete an MDL project"""
        success = await self.project_repo.delete(project_id)
        if not success:
            raise NotFoundError(f"MDL project not found: {project_id}")

        logger.info(f"Deleted MDL project: {project_id}")
        return True

    # ===== Model Operations =====

    async def get_model(self, model_id: UUID) -> Optional[MDLModelDetailDTO]:
        """Get model by ID"""
        model = await self.model_repo.get_by_id(model_id)
        if not model:
            return None

        # Fetch model entity to get IDs
        from chatbi.domain.mdl.entities import MDLModelEntity
        from sqlalchemy import select

        stmt = select(MDLModelEntity).where(MDLModelEntity.id == model_id)
        result = await self.model_repo.session.execute(stmt)
        entity = result.scalars().first()

        return MDLModelDetailDTO(
            id=entity.id,
            project_id=entity.project_id,
            name=model.name,
            display_name=model.display_name,
            description=model.description,
            source_table=model.source_table,
            primary_key=model.primary_key,
            columns=model.columns,
            relationships=model.relationships,
            metadata=model.metadata,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def list_models(self, project_id: UUID) -> List[MDLModelDetailDTO]:
        """List models for a project"""
        models = await self.model_repo.get_by_project(project_id)

        # Fetch entities for IDs
        from chatbi.domain.mdl.entities import MDLModelEntity
        from sqlalchemy import select

        stmt = select(MDLModelEntity).where(MDLModelEntity.project_id == project_id)
        result = await self.model_repo.session.execute(stmt)
        entities = {e.id: e for e in result.scalars().all()}

        result_list = []
        for model in models:
            # Find matching entity (match by name if needed)
            entity = next(
                (e for e in entities.values() if e.name == model.name), None
            )
            if entity:
                result_list.append(
                    MDLModelDetailDTO(
                        id=entity.id,
                        project_id=entity.project_id,
                        name=model.name,
                        display_name=model.display_name,
                        description=model.description,
                        source_table=model.source_table,
                        primary_key=model.primary_key,
                        columns=model.columns,
                        relationships=model.relationships,
                        metadata=model.metadata,
                        created_at=entity.created_at,
                        updated_at=entity.updated_at,
                    )
                )

        return result_list

    async def create_model(
        self, project_id: UUID, dto: CreateMDLModelDTO
    ) -> MDLModelDetailDTO:
        """Create a new MDL model"""
        # Verify project exists
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise NotFoundError(f"MDL project not found: {project_id}")

        model = MDLModel(
            name=dto.name,
            display_name=dto.display_name,
            description=dto.description,
            source_table=dto.source_table,
            primary_key=dto.primary_key,
            columns=dto.columns,
            relationships=dto.relationships,
            metadata=dto.metadata or {},
        )

        created = await self.model_repo.create(model, project_id)
        logger.info(f"Created MDL model: {dto.name} in project {project_id}")

        # Fetch entity for IDs
        from chatbi.domain.mdl.entities import MDLModelEntity
        from sqlalchemy import select

        stmt = select(MDLModelEntity).where(
            MDLModelEntity.project_id == project_id,
            MDLModelEntity.name == dto.name
        )
        result = await self.model_repo.session.execute(stmt)
        entity = result.scalars().first()

        return MDLModelDetailDTO(
            id=entity.id,
            project_id=entity.project_id,
            name=created.name,
            display_name=created.display_name,
            description=created.description,
            source_table=created.source_table,
            primary_key=created.primary_key,
            columns=created.columns,
            relationships=created.relationships,
            metadata=created.metadata,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def update_model(
        self, model_id: UUID, dto: UpdateMDLModelDTO
    ) -> MDLModelDetailDTO:
        """Update an MDL model"""
        update_data = dto.model_dump(exclude_unset=True)
        updated = await self.model_repo.update(model_id, **update_data)
        if not updated:
            raise NotFoundError(f"MDL model not found: {model_id}")

        logger.info(f"Updated MDL model: {model_id}")

        # Fetch entity for IDs
        from chatbi.domain.mdl.entities import MDLModelEntity
        from sqlalchemy import select

        stmt = select(MDLModelEntity).where(MDLModelEntity.id == model_id)
        result = await self.model_repo.session.execute(stmt)
        entity = result.scalars().first()

        return MDLModelDetailDTO(
            id=entity.id,
            project_id=entity.project_id,
            name=updated.name,
            display_name=updated.display_name,
            description=updated.description,
            source_table=updated.source_table,
            primary_key=updated.primary_key,
            columns=updated.columns,
            relationships=updated.relationships,
            metadata=updated.metadata,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def delete_model(self, model_id: UUID) -> bool:
        """Delete an MDL model"""
        success = await self.model_repo.delete(model_id)
        if not success:
            raise NotFoundError(f"MDL model not found: {model_id}")

        logger.info(f"Deleted MDL model: {model_id}")
        return True
