import dspy
from typing import Literal

class IntentSignature(dspy.Signature):
    """
    Classify the user's question intent.
    """
    
    question = dspy.InputField(desc="The user's question or request")
    context = dspy.InputField(desc="Previous conversation context", optional=True)
    
    intent = dspy.OutputField(desc="One of: 'query', 'greeting', 'help', 'clarification', 'unknown'")
    reasoning = dspy.OutputField(desc="Brief explanation for the classification")

class AmbiguityDetectionSignature(dspy.Signature):
    """
    Analyze if the user's question is CRITICALLY ambiguous.
    
    Guidelines:
    - ONLY mark as ambiguous if the question has NO clear intent or target.
    - Questions like 'top 5 products by sales' are CLEAR even without knowing the database schema.
    - Questions like 'show me something' or 'give me data' are AMBIGUOUS.
    - If a metric/dimension/filter can be reasonably inferred from context, it's NOT ambiguous.
    - Prefer returning False (not ambiguous) unless absolutely certain.
    """
    
    question = dspy.InputField(desc="The user's question or request")
    
    is_ambiguous = dspy.OutputField(desc="True ONLY if the question is impossibly vague (e.g., 'show me data' with no subject). False for concrete business questions even if we don't know the exact table structure.")
    ambiguity_type = dspy.OutputField(desc="Type of ambiguity: 'completely_vague', 'multiple_interpretations', 'missing_critical_context', 'none'. Use 'none' for 99% of business queries.")
    clarification_question = dspy.OutputField(desc="A question to ask the user to clarify their intent (only if is_ambiguous=True)")
    options = dspy.OutputField(desc="List of potential options to present to the user (empty list if is_ambiguous=False)")
