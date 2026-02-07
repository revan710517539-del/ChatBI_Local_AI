"""
Ask Pipeline

Complete GenBI question answering pipeline that orchestrates:
1. Intent Classification
2. MDL Retrieval (semantic layer context)
3. Query Reasoning (with streaming)
4. Cube Query Generation
5. Query Validation & Correction
6. Query Execution
7. Answer Generation

Supports streaming output for real-time frontend updates.
"""

from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime
import json

from loguru import logger

from chatbi.agent.intent_agent import IntentClassificationAgent
from chatbi.agent.reasoning_agent import QueryReasoningAgent
from chatbi.agent.chart_agent import ChartGenerationAgent
from chatbi.agent.answer_agent import AnswerSummarizationAgent
from chatbi.pipelines.retrieval.mdl_retrieval import MDLRetrievalPipeline
from chatbi.pipelines.retrieval.history_retrieval import HistoricalQuestionRetrieval
from chatbi.agent.llm.base_llm import BaseLLM
from chatbi.observability import LangfuseObserver


class AskPipeline:
    """Complete question answering pipeline"""

    def __init__(
        self,
        llm: BaseLLM,
        qdrant_manager,
        observer: Optional[LangfuseObserver] = None,
    ):
        """
        Initialize Ask Pipeline

        Args:
            llm: LLM provider for agents
            qdrant_manager: Qdrant manager for MDL retrieval
            observer: Langfuse observer for tracing (optional)
        """
        self.llm = llm
        self.qdrant_manager = qdrant_manager
        self.observer = observer or LangfuseObserver()

        # Initialize agents with observer
        self.intent_agent = IntentClassificationAgent(llm, observer=self.observer)
        self.reasoning_agent = QueryReasoningAgent(llm, observer=self.observer)
        self.chart_agent = ChartGenerationAgent(llm, observer=self.observer)
        self.answer_agent = AnswerSummarizationAgent(llm, observer=self.observer)

        # Initialize pipelines
        self.mdl_retrieval = MDLRetrievalPipeline(qdrant_manager, llm)
        self.history_retrieval = HistoricalQuestionRetrieval(qdrant_manager, llm)

        logger.info("AskPipeline initialized with Langfuse observer")

    async def run(
        self,
        question: str,
        project_id: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        language: str = "zh-CN",
        max_correction_attempts: int = 2,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run complete question answering pipeline with streaming

        Args:
            question: User's natural language question
            project_id: MDL project ID
            session_id: Optional session ID for context
            user_id: Optional user ID
            language: Response language (zh-CN or en-US)
            max_correction_attempts: Max query correction retries

        Yields:
            Event dicts with type and content:
            - {"type": "intent", "content": "query", ...}
            - {"type": "reasoning", "content": "Step 1: ...", ...}
            - {"type": "mdl_context", "content": "...", ...}
            - {"type": "cube_query", "content": {...}, ...}
            - {"type": "validation", "content": "valid", ...}
            - {"type": "correction", "content": {...}, ...}
            - {"type": "result", "content": {...}, ...}
            - {"type": "error", "content": "...", ...}
            - {"type": "done", ...}
        """
        start_time = datetime.now()
        logger.info(f"AskPipeline starting for question: {question[:100]}...")

        try:
            # Step 1: Intent Classification
            logger.info("Step 1: Classifying intent...")
            intent_msg = await self.intent_agent.replay(question)
            intent = intent_msg.content

            yield {
                "type": "intent",
                "content": intent,
                "metadata": intent_msg.metadata,
            }

            # Handle non-query intents
            if intent in ["greeting", "help"]:
                answer = self._handle_non_query(intent, language)
                yield {
                    "type": "answer",
                    "content": answer,
                    "intent": intent,
                }
                yield {"type": "done", "session_id": session_id}
                return

            if intent == "clarification":
                yield {
                    "type": "answer",
                    "content": self._get_clarification_message(language),
                    "intent": intent,
                }
                yield {"type": "done", "session_id": session_id}
                return

            # Step 2: MDL Retrieval
            logger.info("Step 2: Retrieving MDL context...")
            mdl_context = await self.mdl_retrieval.run(
                question=question, project_id=project_id, top_k=5, score_threshold=0.6
            )

            yield {
                "type": "mdl_context",
                "content": mdl_context,
                "length": len(mdl_context),
            }

            # Step 2.5: Historical Question Retrieval
            logger.info("Step 2.5: Retrieving similar historical questions...")
            history_queries = await self.history_retrieval.retrieve(
                question=question, project_id=project_id, top_k=3, score_threshold=0.7
            )

            if history_queries:
                yield {
                    "type": "history_context",
                    "content": history_queries,
                    "length": len(history_queries),
                }

            # Step 3: Session Context (for multi-turn)
            session_context = ""
            if session_id:
                from chatbi.pipelines.ask.session_manager import get_session_manager

                session_manager = get_session_manager()
                session_context = session_manager.get_context(session_id, max_messages=3) or ""

                if session_context:
                    yield {
                        "type": "session_context",
                        "content": session_context,
                        "length": len(session_context),
                    }

            # Step 4: Query Reasoning (Streaming)
            logger.info("Step 4: Generating reasoning plan...")
            reasoning_text = ""

            # Combine all context
            full_context = f"{mdl_context}\n\n{history_queries}"
            if session_context:
                full_context = f"{full_context}\n\n{session_context}"

            async for reasoning_chunk in self.reasoning_agent.run_streaming(
                question=question,
                mdl_context=full_context,
                history_queries="",  # Already included in full_context
            ):
                reasoning_text += reasoning_chunk.content
                yield {
                    "type": "reasoning",
                    "content": reasoning_chunk.content,
                    "stream": True,
                }

            # Step 4: Query Generation (TODO: Implement SQL generation)
            logger.warning("Cube.js has been removed. SQL generation is pending implementation.")
            
            yield {
                "type": "answer",
                "content": "Cube.js module has been removed. Please implement SQL generation agent.",
            }

            yield {
                "type": "done",
                "session_id": session_id,
                "total_time_ms": 0,
            }

        except Exception as e:
            logger.error(f"AskPipeline failed: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": str(e),
                "error_type": "pipeline_error",
            }
            yield {"type": "done", "session_id": session_id}

    def _handle_non_query(self, intent: str, language: str) -> str:
        """Handle non-query intents"""
        if intent == "greeting":
            if language == "zh-CN":
                return "你好！我是ChatBI智能分析助手，可以帮助你分析数据、生成报表。请问有什么可以帮助你的？"
            else:
                return "Hello! I'm ChatBI, your intelligent data analysis assistant. How can I help you today?"

        elif intent == "help":
            if language == "zh-CN":
                return """我可以帮助你：
1. 分析业务数据（如：销售额、用户数、订单数等）
2. 生成可视化图表
3. 回答关于数据的问题

例如：
- "过去一个月的销售额是多少？"
- "哪个产品销量最高？"
- "各地区用户数对比"

请随时提出你的问题！"""
            else:
                return """I can help you with:
1. Analyzing business data (sales, users, orders, etc.)
2. Generating visualizations
3. Answering data-related questions

Examples:
- "What's the total revenue for last month?"
- "Which product has the highest sales?"
- "Compare user count across regions"

Feel free to ask any question!"""

        return ""

    def _get_clarification_message(self, language: str) -> str:
        """Get clarification request message"""
        if language == "zh-CN":
            return "抱歉，我没有完全理解你的问题。能否提供更多细节？例如：具体的时间范围、指标名称、筛选条件等。"
        else:
            return "Sorry, I didn't fully understand your question. Could you provide more details? For example: specific time range, metric names, filter conditions, etc."

    def _generate_simple_answer(
        self, question: str, result: Dict[str, Any], language: str
    ) -> str:
        """
        Generate simple natural language answer (placeholder for M4)

        TODO: Replace with AnswerSummarizationAgent in M4
        """
        row_count = result["row_count"]
        execution_time = result["execution_time_ms"]

        if language == "zh-CN":
            return f"查询成功！找到 {row_count} 条记录，耗时 {execution_time}ms。详细数据请查看下方表格。"
        else:
            return f"Query successful! Found {row_count} records in {execution_time}ms. See detailed data below."
