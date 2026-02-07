"""
MDL Data Transfer Objects (DTOs)

API request/response schemas for MDL endpoints
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from chatbi.domain.mdl.models import MDLColumn, MDLMetric, MDLModel, MDLRelationship


class CreateMDLProjectDTO(BaseModel):
    """Request DTO for creating an MDL project"""

    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    datasource_id: UUID = Field(..., description="Associated datasource ID")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Sales Analytics",
                "description": "MDL for sales data analysis",
                "datasource_id": "123e4567-e89b-12d3-a456-426614174001",
            }
        }


class UpdateMDLProjectDTO(BaseModel):
    """Request DTO for updating an MDL project"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    metrics: Optional[List[MDLMetric]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Sales Analytics",
                "description": "Updated description",
            }
        }


class MDLProjectDTO(BaseModel):
    """Response DTO for MDL project"""

    id: UUID
    name: str
    description: Optional[str]
    datasource_id: UUID
    owner_id: UUID
    models_count: int = Field(..., description="Number of models in this project")
    metrics_count: int = Field(..., description="Number of metrics in this project")
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Sales Analytics",
                "description": "MDL for sales data analysis",
                "datasource_id": "123e4567-e89b-12d3-a456-426614174001",
                "owner_id": "123e4567-e89b-12d3-a456-426614174002",
                "models_count": 5,
                "metrics_count": 10,
                "created_at": "2025-12-16T10:00:00Z",
                "updated_at": "2025-12-16T10:00:00Z",
            }
        }


class MDLProjectDetailDTO(BaseModel):
    """Detailed response DTO with full models and metrics"""

    id: UUID
    name: str
    description: Optional[str]
    datasource_id: UUID
    owner_id: UUID
    models: List[MDLModel]
    metrics: List[MDLMetric]
    created_at: datetime
    updated_at: datetime


class CreateMDLModelDTO(BaseModel):
    """Request DTO for creating an MDL model"""

    name: str = Field(..., min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    source_table: str = Field(..., min_length=1, max_length=200)
    primary_key: str = Field(..., min_length=1, max_length=100)
    columns: List[MDLColumn] = Field(default_factory=list)
    relationships: List[MDLRelationship] = Field(default_factory=list)
    metadata: Optional[Dict] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Customers",
                "display_name": "Customer Records",
                "description": "Customer master data",
                "source_table": "public.customers",
                "primary_key": "id",
                "columns": [],
                "relationships": [],
            }
        }


class UpdateMDLModelDTO(BaseModel):
    """Request DTO for updating an MDL model"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    source_table: Optional[str] = Field(None, min_length=1, max_length=200)
    primary_key: Optional[str] = Field(None, min_length=1, max_length=100)
    columns: Optional[List[MDLColumn]] = None
    relationships: Optional[List[MDLRelationship]] = None
    metadata: Optional[Dict] = None


class MDLModelDTO(BaseModel):
    """Response DTO for MDL model"""

    id: UUID
    project_id: UUID
    name: str
    display_name: Optional[str]
    description: Optional[str]
    source_table: str
    primary_key: str
    columns_count: int = Field(..., description="Number of columns")
    created_at: datetime
    updated_at: datetime


class MDLModelDetailDTO(BaseModel):
    """Detailed response DTO with full columns and relationships"""

    id: UUID
    project_id: UUID
    name: str
    display_name: Optional[str]
    description: Optional[str]
    source_table: str
    primary_key: str
    columns: List[MDLColumn]
    relationships: List[MDLRelationship]
    metadata: Optional[Dict]
    created_at: datetime
    updated_at: datetime


class MDLSyncRequestDTO(BaseModel):
    """Request DTO for MDL sync operation"""

    project_id: UUID = Field(..., description="Project ID to sync")
    datasource_id: UUID = Field(..., description="Datasource ID")
    force_refresh: bool = Field(
        False, description="Force refresh (clear existing MDL)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "datasource_id": "123e4567-e89b-12d3-a456-426614174001",
                "force_refresh": False,
            }
        }


class MDLSyncResponseDTO(BaseModel):
    """Response DTO for MDL sync operation"""

    status: str = Field(..., description="Sync status: success | failed")
    models_count: int = Field(..., description="Number of models indexed")
    indexed_documents: int = Field(..., description="Number of documents in vector DB")
    elapsed_time_ms: int = Field(..., description="Elapsed time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "models_count": 15,
                "indexed_documents": 150,
                "elapsed_time_ms": 5000,
            }
        }
