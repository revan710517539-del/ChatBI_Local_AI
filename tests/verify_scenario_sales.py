
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, Mock
from chatbi.domain.chat.service import ChatService
from chatbi.domain.chat.dtos import ChatDTO
from chatbi.agent.agent_message import AgentMessage

# Mock the Agent classes to prevent real initialization (which might need API keys)
class MockAgent:
    def __init__(self, *args, **kwargs): pass
    def reply(self, *args, **kwargs): return AgentMessage(agent_name="mock", content="", answer="")
    async def replay(self, *args, **kwargs): return AgentMessage(agent_name="mock", content="", answer="")

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.anyio
async def test_sales_scenario_e2e_logic():
    print("\n🚀 Starting E2E Logic Verification for 'Top 5 Products'...")

    # 1. Instantiate Service
    # We pass a mock repo. The service inits real agents, which is fine as long as we mock their methods immediately
    # OR we patch the classes. Let's patch instances for simplicity.
    repo = MagicMock()
    
    # We need to withstand the Service __init__ which creates agents
    # Assuming Agent __init__ doesn't hit network. If it does, we'd need to patch classes.
    # Looking at code: AgentBase.__init__ creates LLM provider. This might fail if no keys.
    # So we MUST patch the Agent classes during import or setup.
    
    with (
        patch('chatbi.domain.chat.service.SchemaAgent', MockAgent),
        patch('chatbi.domain.chat.service.SqlAgent', MockAgent),
        patch('chatbi.domain.chat.service.VisualizeAgent', MockAgent),
        patch('chatbi.domain.chat.service.DiagnosisAgent', MockAgent),
        patch('chatbi.domain.chat.service.IntentClassificationAgent', MockAgent),
    ):
        service = ChatService(repo=repo)
        
        # 2. Setup Behavior for "Top 5 Products"
        
        # A. Intent: QUERY
        service.intent_agent.replay = AsyncMock(return_value=AgentMessage(
            agent_name="intent", 
            intent="query", 
            content="Top 5 products", 
            answer="Top 5 products"
        ))
        
        # B. Schema: Found relevant tables
        service.schema_agent.reply = Mock(return_value=AgentMessage(
            agent_name="schema", 
            answer=[{"name": "products"}, {"name": "orders"}]
        ))
        
        # C. SQL Generation: Correct aggregation
        expected_sql = "SELECT p.product_name, SUM(o.amount) as total_sales FROM orders o JOIN products p ON o.product_id = p.id GROUP BY p.product_name ORDER BY total_sales DESC LIMIT 5"
        service.sql_agent.reply = Mock(return_value=AgentMessage(
            agent_name="sql", 
            answer=expected_sql
        ))
        
        # D. SQL Execution (Mocked)
        mock_run_data = MagicMock()
        mock_run_data.data = '[{"product_name": "iPhone 15", "total_sales": 1000}, {"product_name": "MacBook Pro", "total_sales": 800}]'
        mock_run_data.executed_sql = expected_sql
        mock_run_data.should_visualize = True
        
        # Insight
        mock_run_data.insight = MagicMock()
        mock_run_data.insight.model_dump.return_value = {
            "summary": "iPhone 15 leads sales performance.",
            "key_points": [
                "Total sales volume concentrated in top 2 products.",
                "Significant drop-off after rank 3."
            ]
        }
        
        # Mock the run_sql method entirely to bypass DB
        service.run_sql = AsyncMock(return_value=mock_run_data)
        
        # E. Visualization
        service.visualize_agent.reply = Mock(return_value=AgentMessage(
            agent_name="visualize", 
            answer={
                "type": "interval", 
                "title": "Top 5 Products", 
                "data": {"values": []} # Simplified
            }
        ))

        # 3. Simulate Request
        dto = ChatDTO(id="session-1", question="销售量最高的前 5 个产品", text="销售量最高的前 5 个产品")
        request = MagicMock()
        
        # 4. Run Analysis
        result = await service.analysis(request, dto)
        
        # 5. Verify Frontend Contract
        print("\n🔍 Verifying Response Structure...")
        
        # Check Intent
        print(f"  - Intent: {result.get('intent')}")
        assert result.get('intent') == 'query'
        
        # Check SQL
        executed_sql = result.get('executed_sql')
        print(f"  - Generated SQL: {executed_sql}")
        assert executed_sql == expected_sql
        
        # Check Insight
        insight = result.get('insight', {})
        print(f"  - Insight Summary: {insight.get('summary')}")
        assert insight.get('summary') == "iPhone 15 leads sales performance."
        print(f"  - Insight KeyPoints: {len(insight.get('key_points', []))} points")
        assert len(insight.get('key_points')) == 2
        
        # Check Chart
        chart_config = result.get('visualize_config', {})
        print(f"  - Chart Type: {chart_config.get('type')}")
        assert chart_config.get('type') == 'interval'
        
        print("\n✅ Verification Successful: Backend correctly processes 'Top 5 Products' request.")

from unittest.mock import patch

if __name__ == "__main__":
    asyncio.run(test_sales_scenario_e2e_logic())
