from sqlalchemy import Boolean, Column, Integer, JSON, String, Text
from chatbi.domain.common import UUIDModel
from chatbi.domain.diagnosis.models import CorrectionLog as CorrectionLogDomain
from chatbi.domain.diagnosis.models import DiagnosisResult as DiagnosisResultDomain


class DiagnosisResult(UUIDModel):
    """
    ORM entity for Diagnosis Result.
    """
    __tablename__ = "diagnosis_results"

    query_id = Column(String(36), index=True, nullable=False)
    summary = Column(Text, nullable=False)
    key_points = Column(JSON, nullable=False)

    def to_domain_model(self) -> DiagnosisResultDomain:
        return DiagnosisResultDomain(
            id=self.id,
            query_id=self.query_id,
            summary=self.summary,
            key_points=self.key_points,
            created_at=self.created_at,
        )


class CorrectionLog(UUIDModel):
    """
    ORM entity for Correction Log.
    """
    __tablename__ = "correction_logs"

    query_id = Column(String(36), index=True, nullable=False)
    attempt_number = Column(Integer, nullable=False)
    original_sql = Column(Text, nullable=False)
    error_message = Column(Text, nullable=False)
    corrected_sql = Column(Text, nullable=True)
    was_successful = Column(Boolean, nullable=False)

    def to_domain_model(self) -> CorrectionLogDomain:
        return CorrectionLogDomain(
            id=self.id,
            query_id=self.query_id,
            attempt_number=self.attempt_number,
            original_sql=self.original_sql,
            error_message=self.error_message,
            corrected_sql=self.corrected_sql,
            was_successful=self.was_successful,
            created_at=self.created_at,
        )
