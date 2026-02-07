"""
MDL SQLAlchemy ORM Entities

Maps domain models to database tables:
- MDLProjectEntity → mdl_projects
- MDLModelEntity → mdl_models
- MDLColumnEntity → mdl_columns
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from chatbi.domain.common.entities import Base
from chatbi.domain.mdl.models import (
    MDLColumn,
    MDLMetric,
    MDLModel,
    MDLProject,
    MDLRelationship,
)


class MDLProjectEntity(Base):
    """ORM entity for mdl_projects table"""

    __tablename__ = "mdl_projects"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    datasource_id = Column(String(36), ForeignKey("datasources.id", ondelete="CASCADE"), nullable=False)
    owner_id = Column(PGUUID(as_uuid=True), ForeignKey("app_users.id"), nullable=False)
    meta_data = Column(JSON, nullable=True)  # Stores metrics and other metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    models = relationship("MDLModelEntity", back_populates="project", cascade="all, delete-orphan")

    def to_domain(self) -> MDLProject:
        """Convert ORM entity to domain model"""
        # Extract metrics from meta_data
        metrics_data = self.meta_data.get("metrics", []) if self.meta_data else []
        metrics = [MDLMetric(**m) for m in metrics_data]

        # Convert models
        domain_models = [model.to_domain() for model in self.models] if self.models else []

        return MDLProject(
            id=self.id,
            name=self.name,
            description=self.description,
            datasource_id=self.datasource_id,
            owner_id=self.owner_id,
            models=domain_models,
            metrics=metrics,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, project: MDLProject) -> "MDLProjectEntity":
        """Create ORM entity from domain model"""
        # Store metrics in meta_data
        meta_data = {"metrics": [m.model_dump() for m in project.metrics]}

        entity = cls(
            id=project.id,
            name=project.name,
            description=project.description,
            datasource_id=project.datasource_id,
            owner_id=project.owner_id,
            meta_data=meta_data,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
        return entity


class MDLModelEntity(Base):
    """ORM entity for mdl_models table"""

    __tablename__ = "mdl_models"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("mdl_projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    display_name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    source_table = Column(String(200), nullable=False)
    primary_key = Column(String(100), nullable=False)
    meta_data = Column(JSON, nullable=True)  # Stores relationships and other metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("MDLProjectEntity", back_populates="models")
    columns = relationship("MDLColumnEntity", back_populates="model", cascade="all, delete-orphan")

    def to_domain(self) -> MDLModel:
        """Convert ORM entity to domain model"""
        # Extract relationships from meta_data
        relationships_data = self.meta_data.get("relationships", []) if self.meta_data else []
        relationships = [MDLRelationship(**r) for r in relationships_data]

        # Convert columns
        columns = [col.to_domain() for col in self.columns] if self.columns else []

        # Extract additional metadata (excluding relationships)
        extra_metadata = {k: v for k, v in (self.meta_data or {}).items() if k != "relationships"}

        return MDLModel(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            source_table=self.source_table,
            primary_key=self.primary_key,
            columns=columns,
            relationships=relationships,
            metadata=extra_metadata,
        )

    @classmethod
    def from_domain(cls, model: MDLModel, project_id: UUID) -> "MDLModelEntity":
        """Create ORM entity from domain model"""
        # Store relationships in meta_data
        meta_data = {"relationships": [r.model_dump() for r in model.relationships]}
        # Merge additional metadata
        meta_data.update(model.metadata or {})

        entity = cls(
            project_id=project_id,
            name=model.name,
            display_name=model.display_name,
            description=model.description,
            source_table=model.source_table,
            primary_key=model.primary_key,
            meta_data=meta_data,
        )
        return entity


class MDLColumnEntity(Base):
    """ORM entity for mdl_columns table"""

    __tablename__ = "mdl_columns"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    model_id = Column(PGUUID(as_uuid=True), ForeignKey("mdl_models.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    display_name = Column(String(200), nullable=True)
    column_type = Column(String(20), nullable=False)  # dimension | measure | calculated
    data_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    expression = Column(Text, nullable=True)  # For calculated fields
    aggregation = Column(String(20), nullable=True)  # sum, avg, count, etc.
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    model = relationship("MDLModelEntity", back_populates="columns")

    def to_domain(self) -> MDLColumn:
        """Convert ORM entity to domain model"""
        return MDLColumn(
            name=self.name,
            display_name=self.display_name,
            column_type=self.column_type,
            data_type=self.data_type,
            description=self.description,
            expression=self.expression,
            aggregation=self.aggregation,
            metadata=self.meta_data or {},
        )

    @classmethod
    def from_domain(cls, column: MDLColumn, model_id: UUID) -> "MDLColumnEntity":
        """Create ORM entity from domain model"""
        return cls(
            model_id=model_id,
            name=column.name,
            display_name=column.display_name,
            column_type=column.column_type,
            data_type=column.data_type,
            description=column.description,
            expression=column.expression,
            aggregation=column.aggregation,
            meta_data=column.metadata,
        )
