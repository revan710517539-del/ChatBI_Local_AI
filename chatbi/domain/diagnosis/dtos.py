from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class DiagnosisDTO(BaseModel):
    """
    Data Transfer Object for Diagnosis Result.
    """
    id: UUID
    query_id: UUID
    summary: str
    key_points: List[str]


class InsightSummary(BaseModel):
    """
    Summary of the insight generated.
    """
    summary: str
    key_points: List[str]


class CreateDiagnosisDTO(BaseModel):
    """
    DTO for creating a diagnosis.
    """
    query_id: UUID
    summary: str
    key_points: List[str]


class CorrectionLogDTO(BaseModel):
    """
    Data Transfer Object for Correction Log.
    """
    id: UUID
    query_id: UUID
    attempt_number: int
    original_sql: str
    error_message: str
    corrected_sql: Optional[str]
    was_successful: bool

