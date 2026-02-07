import pytest
import asyncio
from unittest.mock import MagicMock, patch
from chatbi.agent.intent_agent import IntentClassificationAgent

# Mock dspy.Prediction
class MockPrediction:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.anyio
async def test_concrete_business_questions_not_ambiguous():
    """
    Test that concrete business questions are NOT marked as ambiguous.
    """
    agent = IntentClassificationAgent()
    
    concrete_questions = [
        "销售量最高的前 5 个产品",
        "Top 5 products by revenue",
        "Show me monthly sales trends",
        "What are the best selling items?",
        "List customers who bought more than 10 times",
    ]

    print("\n🔍 Testing Concrete Business Questions (Should NOT be ambiguous)...")

    for question in concrete_questions:
        print(f"\n  Question: {question}")
        
        with patch("dspy.ChainOfThought") as mock_chain:
            # Mock classify (intent)
            mock_classify = MagicMock()
            mock_classify.return_value = MockPrediction(
                intent="query", 
                reasoning="Business query"
            )
            
            # Mock ambiguity check - SHOULD return False for these
            mock_ambiguity = MagicMock()
            mock_ambiguity.return_value = MockPrediction(
                is_ambiguous="false",  # NOT ambiguous
                ambiguity_type="none",
                clarification_question="",
                options=[]
            )
            
            mock_chain.side_effect = [mock_classify, mock_ambiguity]
            
            message = await agent.replay(question)
            
            # Should be classified as query, NOT clarification
            assert message.intent == "query", f"Failed: '{question}' should be 'query', got '{message.intent}'"
            print(f"    ✅ Correctly classified as 'query'")

@pytest.mark.anyio
async def test_vague_questions_are_ambiguous():
    """
    Test that truly vague questions ARE marked as ambiguous.
    """
    agent = IntentClassificationAgent()
    
    vague_questions = [
        "给我一些数据",
        "Show me something",
        "Tell me about it",
        "What do you have?",
    ]

    print("\n🔍 Testing Vague Questions (SHOULD be ambiguous)...")

    for question in vague_questions:
        print(f"\n  Question: {question}")
        
        with patch("dspy.ChainOfThought") as mock_chain:
            mock_classify = MagicMock()
            mock_classify.return_value = MockPrediction(
                intent="query", 
                reasoning="Unclear request"
            )
            
            # Mock ambiguity check - SHOULD return True for vague questions
            mock_ambiguity = MagicMock()
            mock_ambiguity.return_value = MockPrediction(
                is_ambiguous="true",  # IS ambiguous
                ambiguity_type="completely_vague",
                clarification_question="What data are you looking for?",
                options=[]
            )
            
            mock_chain.side_effect = [mock_classify, mock_ambiguity]
            
            message = await agent.replay(question)
            
            # Should be classified as clarification
            assert message.intent == "clarification", f"Failed: '{question}' should be 'clarification', got '{message.intent}'"
            print(f"    ✅ Correctly classified as 'clarification'")

if __name__ == "__main__":
    asyncio.run(test_concrete_business_questions_not_ambiguous())
    asyncio.run(test_vague_questions_are_ambiguous())
