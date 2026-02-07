from typing import List, Optional, Union
from uuid import UUID

from sqlalchemy import select, desc

from chatbi.domain.common.repository import BaseRepository
from chatbi.domain.diagnosis.entities import DiagnosisResult, CorrectionLog


class DiagnosisRepository(BaseRepository[DiagnosisResult]):
    """
    Repository for accessing diagnosis results.
    """
    model_class = DiagnosisResult

    async def get_by_query_id(self, query_id: Union[UUID, str]) -> Optional[DiagnosisResult]:
        """Get diagnosis result by query ID."""
        if isinstance(query_id, UUID):
            query_id = str(query_id)
            
        stmt = select(self.model_class).filter(self.model_class.query_id == query_id)
        
        if self.is_async:
            result = await self.db.execute(stmt)
            return result.scalars().first()
        
        # For sync session, execute directly
        return self.db.execute(stmt).scalars().first()


class CorrectionLogRepository(BaseRepository[CorrectionLog]):
    """
    Repository for accessing correction logs.
    """
    model_class = CorrectionLog

    async def get_by_query_id(self, query_id: Union[UUID, str]) -> List[CorrectionLog]:
        """Get correction logs by query ID."""
        if isinstance(query_id, UUID):
            query_id = str(query_id)

        stmt = select(self.model_class).filter(self.model_class.query_id == query_id).order_by(self.model_class.created_at)
        
        if self.is_async:
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
            
        return list(self.db.execute(stmt).scalars().all())

