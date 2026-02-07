"""
MDL Repository Layer

Provides data access for MDL domain:
- MDLProjectRepository (sync)
- AsyncMDLProjectRepository (async)
- MDLModelRepository (sync)
- AsyncMDLModelRepository (async)
"""

from typing import List, Optional
from uuid import UUID

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload

from chatbi.domain.mdl.entities import (
    MDLColumnEntity,
    MDLModelEntity,
    MDLProjectEntity,
)
from chatbi.domain.mdl.models import MDLColumn, MDLModel, MDLProject


class MDLProjectRepository:
    """Synchronous repository for MDL projects"""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, project_id: UUID) -> Optional[MDLProject]:
        """Get project by ID with models and columns"""
        entity = (
            self.session.query(MDLProjectEntity)
            .options(
                joinedload(MDLProjectEntity.models).joinedload(MDLModelEntity.columns)
            )
            .filter(MDLProjectEntity.id == project_id)
            .first()
        )
        return entity.to_domain() if entity else None

    def get_by_datasource(self, datasource_id: UUID) -> List[MDLProject]:
        """Get all projects for a datasource"""
        entities = (
            self.session.query(MDLProjectEntity)
            .options(
                joinedload(MDLProjectEntity.models).joinedload(MDLModelEntity.columns)
            )
            .filter(MDLProjectEntity.datasource_id == datasource_id)
            .all()
        )
        return [entity.to_domain() for entity in entities]

    def get_by_owner(self, owner_id: UUID) -> List[MDLProject]:
        """Get all projects for an owner"""
        entities = (
            self.session.query(MDLProjectEntity)
            .options(
                joinedload(MDLProjectEntity.models).joinedload(MDLModelEntity.columns)
            )
            .filter(MDLProjectEntity.owner_id == owner_id)
            .all()
        )
        return [entity.to_domain() for entity in entities]

    def get_all(self, skip: int = 0, limit: int = 100) -> List[MDLProject]:
        """Get all projects with pagination"""
        entities = (
            self.session.query(MDLProjectEntity)
            .options(
                joinedload(MDLProjectEntity.models).joinedload(MDLModelEntity.columns)
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [entity.to_domain() for entity in entities]

    def create(self, project: MDLProject) -> MDLProject:
        """Create a new project"""
        entity = MDLProjectEntity.from_domain(project)
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        logger.info(f"Created MDL project: {entity.id}")
        return entity.to_domain()

    def update(self, project_id: UUID, **kwargs) -> Optional[MDLProject]:
        """Update project fields"""
        entity = self.session.query(MDLProjectEntity).filter(
            MDLProjectEntity.id == project_id
        ).first()
        if not entity:
            return None

        for key, value in kwargs.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)

        self.session.commit()
        self.session.refresh(entity)
        logger.info(f"Updated MDL project: {project_id}")
        return entity.to_domain()

    def delete(self, project_id: UUID) -> bool:
        """Delete a project"""
        entity = self.session.query(MDLProjectEntity).filter(
            MDLProjectEntity.id == project_id
        ).first()
        if not entity:
            return False

        self.session.delete(entity)
        self.session.commit()
        logger.info(f"Deleted MDL project: {project_id}")
        return True


class AsyncMDLProjectRepository:
    """Asynchronous repository for MDL projects"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, project_id: UUID) -> Optional[MDLProject]:
        """Get project by ID with models and columns"""
        stmt = (
            select(MDLProjectEntity)
            .options(
                joinedload(MDLProjectEntity.models).joinedload(MDLModelEntity.columns)
            )
            .where(MDLProjectEntity.id == project_id)
        )
        result = await self.session.execute(stmt)
        entity = result.scalars().first()
        return entity.to_domain() if entity else None

    async def get_by_datasource(self, datasource_id: UUID) -> List[MDLProject]:
        """Get all projects for a datasource"""
        stmt = (
            select(MDLProjectEntity)
            .options(
                joinedload(MDLProjectEntity.models).joinedload(MDLModelEntity.columns)
            )
            .where(MDLProjectEntity.datasource_id == datasource_id)
        )
        result = await self.session.execute(stmt)
        entities = result.scalars().all()
        return [entity.to_domain() for entity in entities]

    async def get_by_owner(self, owner_id: UUID) -> List[MDLProject]:
        """Get all projects for an owner"""
        stmt = (
            select(MDLProjectEntity)
            .options(
                joinedload(MDLProjectEntity.models).joinedload(MDLModelEntity.columns)
            )
            .where(MDLProjectEntity.owner_id == owner_id)
        )
        result = await self.session.execute(stmt)
        entities = result.scalars().all()
        return [entity.to_domain() for entity in entities]

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[MDLProject]:
        """Get all projects with pagination"""
        stmt = (
            select(MDLProjectEntity)
            .options(
                joinedload(MDLProjectEntity.models).joinedload(MDLModelEntity.columns)
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        entities = result.scalars().all()
        return [entity.to_domain() for entity in entities]

    async def create(self, project: MDLProject) -> MDLProject:
        """Create a new project"""
        entity = MDLProjectEntity.from_domain(project)
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        logger.info(f"Created MDL project: {entity.id}")
        return entity.to_domain()

    async def update(self, project_id: UUID, **kwargs) -> Optional[MDLProject]:
        """Update project fields"""
        stmt = select(MDLProjectEntity).where(MDLProjectEntity.id == project_id)
        result = await self.session.execute(stmt)
        entity = result.scalars().first()
        if not entity:
            return None

        for key, value in kwargs.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)

        await self.session.commit()
        await self.session.refresh(entity)
        logger.info(f"Updated MDL project: {project_id}")
        return entity.to_domain()

    async def delete(self, project_id: UUID) -> bool:
        """Delete a project"""
        stmt = select(MDLProjectEntity).where(MDLProjectEntity.id == project_id)
        result = await self.session.execute(stmt)
        entity = result.scalars().first()
        if not entity:
            return False

        await self.session.delete(entity)
        await self.session.commit()
        logger.info(f"Deleted MDL project: {project_id}")
        return True


class MDLModelRepository:
    """Synchronous repository for MDL models"""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, model_id: UUID) -> Optional[MDLModel]:
        """Get model by ID with columns"""
        entity = (
            self.session.query(MDLModelEntity)
            .options(joinedload(MDLModelEntity.columns))
            .filter(MDLModelEntity.id == model_id)
            .first()
        )
        return entity.to_domain() if entity else None

    def get_by_project(self, project_id: UUID) -> List[MDLModel]:
        """Get all models for a project"""
        entities = (
            self.session.query(MDLModelEntity)
            .options(joinedload(MDLModelEntity.columns))
            .filter(MDLModelEntity.project_id == project_id)
            .all()
        )
        return [entity.to_domain() for entity in entities]

    def create(self, model: MDLModel, project_id: UUID) -> MDLModel:
        """Create a new model"""
        entity = MDLModelEntity.from_domain(model, project_id)
        self.session.add(entity)

        # Create columns
        for column in model.columns:
            column_entity = MDLColumnEntity.from_domain(column, entity.id)
            self.session.add(column_entity)

        self.session.commit()
        self.session.refresh(entity)
        logger.info(f"Created MDL model: {entity.id}")
        return entity.to_domain()

    def update(self, model_id: UUID, **kwargs) -> Optional[MDLModel]:
        """Update model fields"""
        entity = self.session.query(MDLModelEntity).filter(
            MDLModelEntity.id == model_id
        ).first()
        if not entity:
            return None

        # Handle columns separately if provided
        columns = kwargs.pop("columns", None)
        if columns is not None:
            # Delete existing columns
            self.session.query(MDLColumnEntity).filter(
                MDLColumnEntity.model_id == model_id
            ).delete()
            # Create new columns
            for column in columns:
                column_entity = MDLColumnEntity.from_domain(column, model_id)
                self.session.add(column_entity)

        # Update other fields
        for key, value in kwargs.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)

        self.session.commit()
        self.session.refresh(entity)
        logger.info(f"Updated MDL model: {model_id}")
        return entity.to_domain()

    def delete(self, model_id: UUID) -> bool:
        """Delete a model"""
        entity = self.session.query(MDLModelEntity).filter(
            MDLModelEntity.id == model_id
        ).first()
        if not entity:
            return False

        self.session.delete(entity)
        self.session.commit()
        logger.info(f"Deleted MDL model: {model_id}")
        return True


class AsyncMDLModelRepository:
    """Asynchronous repository for MDL models"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, model_id: UUID) -> Optional[MDLModel]:
        """Get model by ID with columns"""
        stmt = (
            select(MDLModelEntity)
            .options(joinedload(MDLModelEntity.columns))
            .where(MDLModelEntity.id == model_id)
        )
        result = await self.session.execute(stmt)
        entity = result.scalars().first()
        return entity.to_domain() if entity else None

    async def get_by_project(self, project_id: UUID) -> List[MDLModel]:
        """Get all models for a project"""
        stmt = (
            select(MDLModelEntity)
            .options(joinedload(MDLModelEntity.columns))
            .where(MDLModelEntity.project_id == project_id)
        )
        result = await self.session.execute(stmt)
        entities = result.scalars().all()
        return [entity.to_domain() for entity in entities]

    async def create(self, model: MDLModel, project_id: UUID) -> MDLModel:
        """Create a new model"""
        entity = MDLModelEntity.from_domain(model, project_id)
        self.session.add(entity)
        await self.session.flush()  # Get entity.id

        # Create columns
        for column in model.columns:
            column_entity = MDLColumnEntity.from_domain(column, entity.id)
            self.session.add(column_entity)

        await self.session.commit()
        await self.session.refresh(entity)
        logger.info(f"Created MDL model: {entity.id}")
        return entity.to_domain()

    async def update(self, model_id: UUID, **kwargs) -> Optional[MDLModel]:
        """Update model fields"""
        stmt = select(MDLModelEntity).where(MDLModelEntity.id == model_id)
        result = await self.session.execute(stmt)
        entity = result.scalars().first()
        if not entity:
            return None

        # Handle columns separately if provided
        columns = kwargs.pop("columns", None)
        if columns is not None:
            # Delete existing columns
            from sqlalchemy import delete as sql_delete

            delete_stmt = sql_delete(MDLColumnEntity).where(
                MDLColumnEntity.model_id == model_id
            )
            await self.session.execute(delete_stmt)
            # Create new columns
            for column in columns:
                column_entity = MDLColumnEntity.from_domain(column, model_id)
                self.session.add(column_entity)

        # Update other fields
        for key, value in kwargs.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)

        await self.session.commit()
        await self.session.refresh(entity)
        logger.info(f"Updated MDL model: {model_id}")
        return entity.to_domain()

    async def delete(self, model_id: UUID) -> bool:
        """Delete a model"""
        stmt = select(MDLModelEntity).where(MDLModelEntity.id == model_id)
        result = await self.session.execute(stmt)
        entity = result.scalars().first()
        if not entity:
            return False

        await self.session.delete(entity)
        await self.session.commit()
        logger.info(f"Deleted MDL model: {model_id}")
        return True
