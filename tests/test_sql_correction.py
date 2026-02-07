import pytest
from unittest.mock import AsyncMock, Mock, patch
from chatbi.pipelines.execution.execution_pipeline import SQLExecutionPipeline
from chatbi.agent.sql_agent import SqlAgent
from chatbi.domain.diagnosis.repository import CorrectionLogRepository
from chatbi.agent.agent_message import AgentMessage

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.anyio
async def test_execution_pipeline_success_first_try():
    # Setup
    sql_agent = Mock(spec=SqlAgent)
    correction_repo = AsyncMock(spec=CorrectionLogRepository)
    execute_func = AsyncMock(return_value="result")
    
    pipeline = SQLExecutionPipeline(
        sql_agent=sql_agent,
        correction_repo=correction_repo,
        execute_sql_func=execute_func
    )
    
    # Run
    sql = "SELECT * FROM test"
    final_sql, result = await pipeline.run("id", sql, "question", "schema")
    
    # Assert
    assert final_sql == sql
    assert result == "result"
    assert execute_func.call_count == 1
    correction_repo.create.assert_not_called()

@pytest.mark.anyio
async def test_execution_pipeline_retry_success():
    # Setup
    sql_agent = Mock(spec=SqlAgent)
    correction_repo = AsyncMock(spec=CorrectionLogRepository)
    
    # First call fails, second succeeds
    execute_func = AsyncMock(side_effect=[Exception("Syntax error"), "success result"])
    
    # Agent provides correction
    agent_message = Mock(spec=AgentMessage)
    agent_message.answer = "SELECT * FROM corrected"
    sql_agent.reply.return_value = agent_message
    
    pipeline = SQLExecutionPipeline(
        sql_agent=sql_agent,
        correction_repo=correction_repo,
        execute_sql_func=execute_func
    )
    
    # Run
    final_sql, result = await pipeline.run("id", "SELECT * FROM wrong", "question", "schema")
    
    # Assert
    assert final_sql == "SELECT * FROM corrected"
    assert result == "success result"
    assert execute_func.call_count == 2
    
    # Agent was called
    sql_agent.reply.assert_called_once()
    args = sql_agent.reply.call_args[1]
    assert args["previous_sql"] == "SELECT * FROM wrong"
    assert "Syntax error" in args["error_message"]
    
    # Logs were created
    assert correction_repo.create.call_count == 2
    # First log: Failure
    # Second log: Success

@pytest.mark.anyio
async def test_execution_pipeline_max_retries():
    # Setup
    sql_agent = Mock(spec=SqlAgent)
    correction_repo = AsyncMock(spec=CorrectionLogRepository)
    
    # Always fails
    execute_func = AsyncMock(side_effect=Exception("Still wrong"))
    
    # Agent provides correction
    agent_message = Mock(spec=AgentMessage)
    agent_message.answer = "SELECT * FROM corrected"
    sql_agent.reply.return_value = agent_message
    
    pipeline = SQLExecutionPipeline(
        sql_agent=sql_agent,
        correction_repo=correction_repo,
        execute_sql_func=execute_func,
        max_retries=2
    )
    
    # Run and expect exception
    with pytest.raises(Exception) as excinfo:
        await pipeline.run("id", "SELECT * FROM wrong", "question", "schema")
    
    assert "Still wrong" in str(excinfo.value)
    
    # Check calls
    # Attempt 1 (initial) -> Fail
    # Attempt 2 (retry 1) -> Fail
    # Attempt 3 (retry 2) -> Fail -> Raise
    assert execute_func.call_count == 3 
    assert sql_agent.reply.call_count == 2
    assert correction_repo.create.call_count == 3
