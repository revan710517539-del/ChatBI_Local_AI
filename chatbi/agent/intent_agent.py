import json
import ast
import json
import ast
"""
Intent Classification Agent

Classifies user's question intent to route the request appropriately:
- 'query': Data query requiring database access
- 'greeting': Greeting/casual conversation
- 'help': Help/documentation request
- 'clarification': Needs more information

This helps optimize the pipeline by skipping expensive operations for non-query intents.
"""

from typing import Literal, Optional
import dspy
from loguru import logger

from chatbi.agent.agent_base import AgentBase
from chatbi.agent.agent_message import AgentMessage
from chatbi.agent.prompts.intent_prompt import IntentSignature, AmbiguityDetectionSignature


IntentType = Literal["query", "greeting", "help", "clarification", "unknown"]


class IntentClassificationAgent(AgentBase):
    """Agent for classifying user question intent and detecting ambiguity"""

    def __init__(self, llm_provider=None, observer=None):
        super().__init__(name="IntentClassificationAgent", llm_provider=llm_provider, observer=observer)

    async def replay(self, question: str, context: Optional[str] = None, **kwargs) -> AgentMessage:
        """
        Classify user's question intent
        """
        logger.debug(f"[{self.name}]: Analyzing intent for '{question}'")
        
        # 1. First check broad intent
        try:
            classify = dspy.ChainOfThought(IntentSignature)
            response = classify(question=question, context=context)
            intent = response.intent.lower().strip()
            reasoning = response.reasoning
            
            logger.info(f"[{self.name}]: Classified as '{intent}' ({reasoning})")
            
            # Map standard intents if needed
            valid_intents = ["query", "greeting", "help", "clarification", "unknown"]
            if intent not in valid_intents:
                # Naive mapping
                if "query" in intent or "data" in intent:
                    intent = "query"
                else:
                    intent = "unknown"

            # 2. If intent is query, check for ambiguity
            if intent == "query":
                check_ambiguity = dspy.ChainOfThought(AmbiguityDetectionSignature)
                ambiguity_res = check_ambiguity(question=question)
                
                # Check if it's strictly True
                is_ambiguous = str(ambiguity_res.is_ambiguous).lower() == "true"

                if is_ambiguous:
                    logger.info(f"[{self.name}]: Ambiguity detected: {ambiguity_res.ambiguity_type}")
                    
                    # Safe parsing of options
                    raw_options = ambiguity_res.options
                    options = []
                    if isinstance(raw_options, list):
                        options = raw_options
                    elif isinstance(raw_options, str):
                        try:
                            # Try json parse first
                            options = json.loads(raw_options)
                        except:
                            try:
                                # Try literal eval (e.g. single quotes)
                                options = ast.literal_eval(raw_options)
                            except:
                                logger.warning(f"Could not parse options string: {raw_options}")
                                options = []
                    
                    # Ensure it's a list of dicts with label/value
                    if not isinstance(options, list):
                         options = []
                         
                    return AgentMessage(
                        agent_name=self.name,
                        content=ambiguity_res.clarification_question,
                        answer=ambiguity_res.clarification_question,
                        intent="clarification",
                        metadata={
                            "reasoning": reasoning,
                            "is_ambiguous": True,
                            "ambiguity_type": ambiguity_res.ambiguity_type,
                            "options": options
                        }
                    )
            
            # Regular response
            return AgentMessage(
                agent_name=self.name,
                content=question,
                intent=intent,
                answer="",
                metadata={"reasoning": reasoning}
            )
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            # Fallback
            return AgentMessage(
                agent_name=self.name,
                content=question,
                intent="unknown",
                answer="I'm not sure how to help with that.",
                metadata={"error": str(e)}
            )

    def classify_sync(self, question: str) -> IntentType:
        """
        Synchronous intent classification (for compatibility)
        """
        import asyncio
        try:
            result = asyncio.run(self.replay(question))
            return result.intent
        except Exception as e:
            logger.error(f"Sync intent classification failed: {e}")
            return "unknown"
