"""
Query Reasoning Agent

Generates step-by-step reasoning plan for query execution with streaming support.

This agent:
1. Analyzes the user's question
2. Identifies required data models, metrics, and filters
3. Breaks down the query into logical steps
4. Provides transparency into the AI's thinking process

Supports streaming for real-time display of reasoning steps.
"""

from typing import AsyncGenerator

from loguru import logger

from chatbi.agent.agent_base import AgentBase
from chatbi.agent.agent_message import AgentMessage


class QueryReasoningAgent(AgentBase):
    """Agent for generating query reasoning plans"""

    def __init__(self, llm_provider, observer=None):
        super().__init__(name="QueryReasoningAgent", llm_provider=llm_provider, observer=observer)

    def _get_prompt(
        self, question: str, mdl_context: str, history_queries: str = ""
    ) -> str:
        """Generate reasoning prompt"""
        return f"""You are a Business Intelligence query planner.

Given a user's question and available data models, generate a DETAILED step-by-step reasoning plan to answer the question.

### AVAILABLE DATA MODELS ###
{mdl_context}

### SIMILAR HISTORICAL QUERIES ###
{history_queries if history_queries else "No historical queries available."}

### USER'S QUESTION ###
{question}

### YOUR TASK ###
Think step-by-step and create a reasoning plan:

1. **Understand the Question**
   - What is the user asking for?
   - What are the key metrics/dimensions involved?
   - What time period or filters are mentioned?

2. **Identify Required Data**
   - Which models/tables are needed?
   - Which columns (measures and dimensions)?
   - What aggregations are required?

3. **Define Query Logic**
   - How to group the data?
   - How to filter the data?
   - How to sort the results?
   - How many rows to return?

4. **Expected Output**
   - What format should the result be in?
   - What chart type is most appropriate?

### OUTPUT FORMAT ###
Write your reasoning in clear, numbered steps. Be specific about model names, column names, and logic.
Use markdown formatting for readability.

Example:
## Step 1: Understanding the Question
The user wants to find the top 5 products by total sales revenue in 2023.

## Step 2: Identify Required Data
- Model: Orders
- Measure: total_amount (aggregation: sum)
- Dimension: product_name
- Time filter: order_date in 2023

## Step 3: Query Logic
- Group by: product_name
- Aggregate: SUM(total_amount)
- Filter: order_date >= 2023-01-01 AND order_date <= 2023-12-31
- Sort: SUM(total_amount) DESC
- Limit: 5

## Step 4: Expected Output
- Top 5 products with their total revenue
- Best chart: Horizontal bar chart
"""

    async def replay(
        self,
        question: str,
        mdl_context: str = "",
        history_queries: str = "",
        session_id: str = None,
        **kwargs,
    ) -> AgentMessage:
        """
        Generate reasoning plan for a query

        Args:
            question: User's natural language question
            mdl_context: Retrieved MDL context (models/columns)
            history_queries: Similar historical queries (optional)
            session_id: Session ID for tracing

        Returns:
            AgentMessage with reasoning plan
        """
        logger.info(f"Generating reasoning for question: {question[:100]}...")

        try:
            prompt = self._get_prompt(question, mdl_context, history_queries)
            
            # Langfuse tracing
            if self.observer:
                with self.observer.trace_llm_call(
                    name=self.name,
                    model=self.llm.model_name,
                    prompt=prompt,
                    session_id=session_id,
                    metadata={"question": question, "has_history": bool(history_queries)},
                ) as ctx:
                    response = await self.llm.generate(prompt, temperature=0.3)
                    ctx["output"] = response
                    # Usage will be filled by LLM if available
            else:
                response = await self.llm.generate(prompt, temperature=0.3)

            logger.info("Reasoning generation completed")

            return AgentMessage(
                agent_name=self.name,
                content=response,
                metadata={
                    "question": question,
                    "mdl_context_length": len(mdl_context),
                    "has_history": bool(history_queries),
                },
            )

        except Exception as e:
            logger.error(f"Reasoning generation failed: {e}")
            return AgentMessage(
                agent_name=self.name,
                content=f"Failed to generate reasoning: {str(e)}",
                metadata={
                    "question": question,
                    "error": str(e),
                },
            )

    async def run_streaming(
        self,
        question: str,
        mdl_context: str = "",
        history_queries: str = "",
        session_id: str = None,
        **kwargs,
    ) -> AsyncGenerator[AgentMessage, None]:
        """
        Generate reasoning plan with streaming output

        Args:
            question: User's natural language question
            mdl_context: Retrieved MDL context
            history_queries: Similar historical queries
            session_id: Session ID for tracing

        Yields:
            AgentMessage chunks with partial reasoning content
        """
        logger.info(
            f"Generating reasoning (streaming) for question: {question[:100]}..."
        )

        try:
            prompt = self._get_prompt(question, mdl_context, history_queries)

            # Stream response from LLM with Langfuse tracing
            accumulated_content = ""
            
            if self.observer:
                stream = self.llm.generate_stream(prompt, temperature=0.3)
                traced_stream = self.observer.trace_llm_streaming(
                    name=self.name,
                    model=self.llm.model_name,
                    prompt=prompt,
                    stream=stream,
                    session_id=session_id,
                    metadata={"question": question, "has_history": bool(history_queries)},
                )
                async for chunk in traced_stream:
                    accumulated_content += chunk
                    yield AgentMessage(
                        agent_name=self.name,
                        content=chunk,
                        metadata={
                            "question": question,
                            "stream": True,
                            "accumulated_length": len(accumulated_content),
                        },
                    )
            else:
                async for chunk in self.llm.generate_stream(prompt, temperature=0.3):
                    accumulated_content += chunk
                    yield AgentMessage(
                        agent_name=self.name,
                        content=chunk,
                        metadata={
                            "question": question,
                            "stream": True,
                            "accumulated_length": len(accumulated_content),
                        },
                    )

            logger.info("Reasoning streaming completed")

        except Exception as e:
            logger.error(f"Reasoning streaming failed: {e}")
            yield AgentMessage(
                agent_name=self.name,
                content=f"Error: {str(e)}",
                metadata={
                    "question": question,
                    "error": str(e),
                    "stream": True,
                },
            )
