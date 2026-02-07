import pytest
from unittest.mock import AsyncMock, Mock, MagicMock
from chatbi.domain.chat.service import ChatService
from chatbi.domain.chat.dtos import ChatDTO
from chatbi.agent.agent_message import AgentMessage

# Define simple AgentMessage helper
def make_msg(content="", intent="", answer="", metadata=None):
    return AgentMessage(
        agent_name="mock", 
        content=content, 
        intent=intent, 
        answer=answer, 
        metadata=metadata or {}
    )

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture
def chat_service():
    repo = MagicMock()
    service = ChatService(repo=repo)
    
    # Mock agents
    service.intent_agent = Mock()
    service.intent_agent.replay = AsyncMock() # replay is async
    
    service.sql_agent = Mock()
    service.sql_agent.reply = Mock() # reply is sync
    
    service.schema_agent = Mock()
    service.schema_agent.reply = Mock()
    
    service.diagnosis_agent = Mock()
    service.diagnosis_agent.reply = Mock()
    
    service.visualize_agent = Mock()
    service.visualize_agent.reply = Mock()
    
    service.cache = Mock()
    service.cache.get.return_value = None
    service.cache.generate_id.return_value = "test-id"
    
    # Mock internal methods that hit DB if necessary, or just mock repo methods
    service.get_table_schema = AsyncMock(return_value=[{"name": "t"}])
    service.run_sql = AsyncMock() # Used in analysis
    
    return service

@pytest.mark.anyio
async def test_ambiguity_flow(chat_service):
    # Setup intent agent to return clarification
    chat_service.intent_agent.replay.return_value = make_msg(
        intent="clarification", 
        content="Ambiguous?",
        metadata={"options": [{"label":"A","value":"a"}]}
    )
    
    request = Mock()
    dto = ChatDTO(id="1", question="Ambiguous question", text="Ambiguous question")
    
    result = await chat_service.analysis(request, dto)
    
    assert result["intent"] == "clarification"
    # Ensure SQL generation was NOT called
    chat_service.sql_agent.reply.assert_not_called()
    # Note: schema agent might be called before intent depending on implementation order, 
    # but in my code I put intent check first (Step 0).
    chat_service.schema_agent.reply.assert_not_called()

@pytest.mark.anyio
async def test_success_flow_with_insight(chat_service):
    # Setup intent agent to return query
    chat_service.intent_agent.replay.return_value = make_msg(intent="query")
    
    # Setup Schema Agent
    chat_service.schema_agent.reply.return_value = make_msg(answer=[{"name": "table"}])
    
    # Setup SQL Agent
    chat_service.sql_agent.reply.return_value = make_msg(answer="SELECT * FROM t")
    
    # Setup Visualization Agent
    chat_service.visualize_agent.reply.return_value = make_msg(answer={"type": "chart"})
    
    # Setup Run SQL result
    mock_run_res = Mock()
    mock_run_res.data = '[{"id": 1}]'
    mock_run_res.should_visualize = True
    mock_run_res.executed_sql = "SELECT * FROM t"
    mock_run_res.insight = Mock()
    mock_run_res.insight.model_dump.return_value = {"summary": "Insight"}
    chat_service.run_sql.return_value = mock_run_res
    
    request = Mock()
    dto = ChatDTO(id="1", question="Query", text="Query", visualize=True)
    
    result = await chat_service.analysis(request, dto)
    
    assert result["intent"] == "query"
    assert result["sql"] == "SELECT * FROM t"
    assert result["insight"]["summary"] == "Insight"
    
    # Check flow 
    chat_service.intent_agent.replay.assert_called_once()
    chat_service.sql_agent.reply.assert_called()
    chat_service.visualize_agent.reply.assert_called()
