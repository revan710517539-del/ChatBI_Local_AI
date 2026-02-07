from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DiagnosisResult(BaseModel):
    """
    Pure domain model for Diagnosis Result.
    """
    id: UUID
    query_id: UUID
    summary: str
    key_points: List[str]
    created_at: datetime = Field(default_factory=datetime.now)


class CorrectionLog(BaseModel):
    """
    Pure domain model for Correction Log.
    """
    id: UUID
    query_id: UUID
    attempt_number: int
    original_sql: str
    error_message: str
    corrected_sql: Optional[str] = None
    was_successful: bool
    created_at: datetime = Field(default_factory=datetime.now)
