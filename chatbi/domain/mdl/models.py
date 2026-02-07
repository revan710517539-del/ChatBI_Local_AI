"""
MDL (Metric Definition Layer) Domain Models

Represents the semantic layer abstractions:
- MDLColumn: Individual column definition (dimension/measure/calculated)
- MDLModel: Business entity with columns and relationships
- MDLProject: Container for multiple models and metrics
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MDLColumn(BaseModel):
    """Represents a column in an MDL model"""

    name: str = Field(..., description="Column name")
    display_name: Optional[str] = Field(None, description="Human-readable name")
    column_type: str = Field(
        ..., description="Column type: dimension | measure | calculated"
    )
    data_type: str = Field(..., description="Data type: string | number | date | boolean")
    description: Optional[str] = Field(None, description="Column description")
    expression: Optional[str] = Field(
        None, description="Expression for calculated fields (e.g., SUM(amount))"
    )
    aggregation: Optional[str] = Field(
        None, description="Aggregation function: sum | avg | count | min | max"
    )
    metadata: Optional[Dict] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "total_amount",
                "display_name": "Total Amount",
                "column_type": "measure",
                "data_type": "number",
                "description": "Sum of order amounts",
                "aggregation": "sum",
            }
        }


class MDLRelationship(BaseModel):
    """Represents a relationship between two MDL models"""

    name: str = Field(..., description="Relationship name")
    target_model: str = Field(..., description="Target model name")
    relationship_type: str = Field(
        ..., description="Relationship type: one_to_many | many_to_one | many_to_many"
    )
    join_column: str = Field(..., description="Column used for join")
    target_column: str = Field(..., description="Target model's join column")
    metadata: Optional[Dict] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "orders",
                "target_model": "Orders",
                "relationship_type": "one_to_many",
                "join_column": "customer_id",
                "target_column": "customer_id",
            }
        }


class MDLModel(BaseModel):
    """Represents a business entity in the semantic layer"""

    name: str = Field(..., description="Model name (e.g., Customers)")
    display_name: Optional[str] = Field(None, description="Human-readable name")
    description: Optional[str] = Field(None, description="Model description")
    source_table: str = Field(..., description="Source table in Cube.js")
    primary_key: str = Field(..., description="Primary key column")
    columns: List[MDLColumn] = Field(default_factory=list, description="Model columns")
    relationships: List[MDLRelationship] = Field(
        default_factory=list, description="Relationships to other models"
    )
    metadata: Optional[Dict] = Field(default_factory=dict, description="Additional metadata")

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


class MDLMetric(BaseModel):
    """Represents a predefined metric (KPI)"""

    name: str = Field(..., description="Metric name")
    display_name: Optional[str] = Field(None, description="Human-readable name")
    description: Optional[str] = Field(None, description="Metric description")
    expression: str = Field(..., description="Metric calculation expression")
    model: str = Field(..., description="Source model name")
    metadata: Optional[Dict] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "total_revenue",
                "display_name": "Total Revenue",
                "description": "Sum of all order amounts",
                "expression": "SUM(Orders.amount)",
                "model": "Orders",
            }
        }


class MDLProject(BaseModel):
    """Container for MDL models and metrics"""

    id: UUID
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    datasource_id: UUID = Field(..., description="Associated datasource ID")
    owner_id: UUID = Field(..., description="Owner user ID")
    models: List[MDLModel] = Field(default_factory=list, description="Models in this project")
    metrics: List[MDLMetric] = Field(
        default_factory=list, description="Predefined metrics"
    )
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
                "models": [],
                "metrics": [],
                "created_at": "2025-12-16T10:00:00Z",
                "updated_at": "2025-12-16T10:00:00Z",
            }
        }
