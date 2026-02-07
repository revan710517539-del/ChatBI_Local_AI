from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from loguru import logger
from sqlalchemy.orm import Session

from chatbi.agent.sql_agent import SqlAgent
from chatbi.domain.diagnosis.entities import CorrectionLog
from chatbi.domain.diagnosis.repository import CorrectionLogRepository
from chatbi.exceptions import DatabaseError


class SQLExecutionPipeline:
    def __init__(
        self,
        sql_agent: SqlAgent,
        correction_repo: CorrectionLogRepository,
        execute_sql_func: Any,  # Function to execute SQL
        max_retries: int = 3,
    ):
        self.sql_agent = sql_agent
        self.correction_repo = correction_repo
        self.execute_sql_func = execute_sql_func
        self.max_retries = max_retries

    async def run(
        self,
        query_id: str,
        initial_sql: str,
        question: str,
        table_schema: str,
    ) -> Tuple[str, Any]:
        """
        Execute SQL with retry logic.

        Args:
            query_id: Query ID (usually ChatSession ID or specific Query ID)
            initial_sql: Initial SQL query to execute
            question: Original user question
            table_schema: Table schema context

        Returns:
            Tuple[str, Any]: (Final SQL, Execution Result)
        """
        current_sql = initial_sql
        last_error = None

        for attempt in range(1, self.max_retries + 2):
            try:
                # Try to execute
                logger.debug(f"Executing SQL (Attempt {attempt}): {current_sql}")
                result = await self.execute_sql_func(current_sql)
                
                # If this was a retry (attempt > 1), log the success
                if attempt > 1:
                    await self._log_attempt(
                        query_id=query_id,
                        attempt=attempt,
                        original_sql=initial_sql if attempt == 2 else current_sql, # Simplified logic
                        error_message=str(last_error) if last_error else "N/A",
                        corrected_sql=current_sql,
                        success=True
                    )
                
                return current_sql, result

            except Exception as e:
                last_error = e
                error_msg = str(e)
                logger.warning(f"SQL Execution failed (Attempt {attempt}): {error_msg}")

                # Log failure
                await self._log_attempt(
                    query_id=query_id,
                    attempt=attempt,
                    original_sql=current_sql,
                    error_message=error_msg,
                    corrected_sql=None,
                    success=False
                )

                if attempt > self.max_retries:
                    logger.error(f"Max retries ({self.max_retries}) reached. Giving up.")
                    raise last_error

                # Generate correction
                logger.info("Requesting SQL correction from agent...")
                try:
                    agent_response = self.sql_agent.reply(
                        id=query_id,
                        question=question,
                        table_schema=table_schema,
                        previous_sql=current_sql,
                        error_message=error_msg
                    )
                    
                    new_sql = agent_response.answer
                    
                    # Clean markdown if present
                    if "```" in new_sql:
                        new_sql = new_sql.replace("```sql", "").replace("```", "").strip()
                        
                    current_sql = new_sql
                    
                except Exception as agent_error:
                    logger.error(f"Agent failed to correct SQL: {agent_error}")
                    raise last_error

        # Should not reach here
        raise last_error

    async def _log_attempt(
        self,
        query_id: str,
        attempt: int,
        original_sql: str,
        error_message: str,
        corrected_sql: Optional[str],
        success: bool
    ):
        try:
            log = CorrectionLog(
                query_id=query_id,
                attempt_number=attempt,
                original_sql=original_sql,
                error_message=error_message,
                corrected_sql=corrected_sql,
                was_successful=success
            )
            await self.correction_repo.create(log)
        except Exception as e:
            logger.error(f"Failed to log correction attempt: {e}")
