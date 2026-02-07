import pytest
import asyncio
from unittest.mock import MagicMock, patch
from chatbi.agent.intent_agent import IntentClassificationAgent


# Mock objects that mimic dspy.Prediction
class MockPrediction:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.mark.anyio
async def test_ambiguity_parsing_robustness():
    """
    Test that IntentAgent correctly parses various formats of 'options'
    returned by the LLM (dspy module)
    """
    agent = IntentClassificationAgent()

    # Test cases for Option Parsing
    test_cases = [
        {
            "name": "Standard List of Dicts",
            "dspy_options": [{"label": "A", "value": "a"}],
            "expected_len": 1,
            "expected_first_val": "a",
        },
        {
            "name": "String Representation of List",
            "dspy_options": "[{'label': 'B', 'value': 'b'}]",
            "expected_len": 1,
            "expected_first_val": "b",
        },
        {
            "name": "JSON String",
            "dspy_options": '[{"label": "C", "value": "c"}]',
            "expected_len": 1,
            "expected_first_val": "c",
        },
        {
            "name": "Empty List",
            "dspy_options": [],
            "expected_len": 0,
            "expected_first_val": None,
        },
        {
            "name": "None",
            "dspy_options": None,
            "expected_len": 0,
            "expected_first_val": None,
        },
        {
            "name": "Garbage String",
            "dspy_options": "This is not a list",
            "expected_len": 0,
            "expected_first_val": None,
        },
    ]

    print("\n[IntentAgent] Starting Robustness Tests...")

    for case in test_cases:
        print(f"Testing Case: {case['name']}")

        # We need to mock dspy.ChainOfThought behavior.
        # The agent calls:
        #   1. classify(question=...)
        #   2. check_ambiguity(question=...)

        with patch("dspy.ChainOfThought") as mock_chain:
            # Mock instances
            mock_classify_instance = MagicMock()
            mock_ambiguity_instance = MagicMock()

            # Setup returns for the two calls
            # 1. Broad Intent
            mock_classify_instance.return_value = MockPrediction(
                intent="query", reasoning="It is a query"
            )

            # 2. Ambiguity Check
            mock_ambiguity_instance.return_value = MockPrediction(
                is_ambiguous="true",
                ambiguity_type="Vague Term",
                clarification_question="What do you mean?",
                options=case["dspy_options"],
            )

            # Configure side_effect to return our specific mocks in order
            mock_chain.side_effect = [mock_classify_instance, mock_ambiguity_instance]

            # Run
            message = await agent.replay("Some question")

            # Assertions
            assert (
                message.intent == "clarification"
            ), f"Failed intent check for {case['name']}"
            options = message.metadata.get("options", [])

            assert isinstance(options, list), f"Options must be list for {case['name']}"
            assert (
                len(options) == case["expected_len"]
            ), f"Length mismatch for {case['name']}. Got {len(options)}"

            if case["expected_len"] > 0:
                assert options[0]["value"] == case["expected_first_val"]

        print(f"✅ Passed: {case['name']}")


if __name__ == "__main__":
    # Allow running directly
    asyncio.run(test_ambiguity_parsing_robustness())
