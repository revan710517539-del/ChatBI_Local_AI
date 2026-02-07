"""
Answer Summarization Agent

Generates natural language summaries from query results with streaming support.

Provides:
- Concise data summaries
- Key insights and findings
- Actionable recommendations (optional)
- Multi-language support (zh-CN, en-US)
"""

from typing import AsyncGenerator, Dict, Any, List

from loguru import logger

from chatbi.agent.agent_base import AgentBase
from chatbi.agent.agent_message import AgentMessage


class AnswerSummarizationAgent(AgentBase):
    """Agent for generating natural language answers"""

    def __init__(self, llm_provider, observer=None):
        super().__init__(name="AnswerSummarizationAgent", llm_provider=llm_provider, observer=observer)

    def _get_prompt(
        self,
        question: str,
        query_metadata: Dict[str, Any],
        result_data: List[Dict],
        chart_config: Dict[str, Any],
        language: str = "zh-CN",
    ) -> str:
        """Generate answer summarization prompt"""
        import json

        lang_instructions = {
            "zh-CN": """你是一个数据分析专家。用简洁、专业的中文总结查询结果。

### 输出要求 ###
1. **开头**: 直接回答用户问题（1-2句话）
2. **数据摘要**: 关键发现和数字（3-5个要点）
3. **洞察**: 数据背后的含义（可选，如果有明显趋势或异常）
4. **语气**: 专业、客观、易懂

### 示例 ###
问题: "2023年销售额最高的5个产品是什么？"

答案:
根据分析，2023年销售额最高的5个产品如下：

**核心发现**:
• 产品A以1,250万元位居榜首，占总销售额的28%
• 前三名产品（A、B、C）贡献了总销售额的65%
• 产品E虽然排名第五，但增长率达到45%，表现突出

**数据详情**:
1. 产品A: ¥12,500,000
2. 产品B: ¥9,800,000
3. 产品C: ¥8,600,000
4. 产品D: ¥6,200,000
5. 产品E: ¥5,500,000

这些产品占据了公司2023年总销售额的75%，是业务的核心驱动力。""",
            "en-US": """You are a data analysis expert. Summarize the query results concisely and professionally.

### OUTPUT REQUIREMENTS ###
1. **Opening**: Directly answer the user's question (1-2 sentences)
2. **Data Summary**: Key findings with numbers (3-5 bullet points)
3. **Insights**: What the data means (optional, if clear trends/anomalies)
4. **Tone**: Professional, objective, clear

### EXAMPLE ###
Question: "What are the top 5 products by sales in 2023?"

Answer:
Based on the analysis, here are the top 5 products by sales in 2023:

**Key Findings**:
• Product A leads with $12.5M, accounting for 28% of total sales
• Top 3 products (A, B, C) contribute 65% of total revenue
• Product E ranks 5th but shows impressive 45% growth rate

**Data Details**:
1. Product A: $12,500,000
2. Product B: $9,800,000
3. Product C: $8,600,000
4. Product D: $6,200,000
5. Product E: $5,500,000

These products represent 75% of the company's 2023 revenue and are core business drivers.""",
        }

        instruction = lang_instructions.get(language, lang_instructions["en-US"])

        return f"""{instruction}

### USER'S QUESTION ###
{question}

### QUERY CONTEXT ###
```json
{json.dumps(query_metadata, indent=2)}
```

### QUERY RESULTS ###
```json
{json.dumps(result_data[:10], indent=2)}
```
Total rows: {len(result_data)}

### CHART TYPE ###
{chart_config.get('chartType', 'table')} - {chart_config.get('description', '')}

### YOUR TASK ###
Write a comprehensive answer following the format above. Focus on:
- Direct answer to the question
- Key numbers and comparisons
- Notable patterns or trends
- Actionable insights (if applicable)

Start writing the answer now:
"""

    async def replay(
        self,
        question: str,
        query_metadata: Dict[str, Any],
        result_data: List[Dict],
        chart_config: Dict[str, Any],
        language: str = "zh-CN",
        **kwargs,
    ) -> AgentMessage:
        """
        Summarize answer from query results

        Args:
            question: User's question
            query_metadata: Executed Query Metadata
            result_data: Query results
            chart_config: Generated chart config
            language: Output language

        Returns:
            AgentMessage with answer text
        """
        logger.info(f"Generating answer for question: {question[:100]}...")

        try:
            prompt = self._get_prompt(
                question=question,
                query_metadata=query_metadata,
                result_data=result_data,
                chart_config=chart_config,
                language=language,
            )

            response = await self.llm.generate(prompt, temperature=0.7)

            logger.info("Answer generation completed")

            return AgentMessage(
                agent_name=self.name,
                content=response,
                metadata={
                    "question": question,
                    "language": language,
                    "answer_length": len(response),
                },
            )

        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            fallback = self._get_fallback_answer(
                result_data=result_data, language=language
            )
            return AgentMessage(
                agent_name=self.name,
                content=fallback,
                metadata={
                    "question": question,
                    "error": str(e),
                    "fallback": True,
                },
            )

    async def run_streaming(
        self,
        question: str,
        query_metadata: Dict[str, Any],
        result_data: List[Dict],
        chart_config: Dict[str, Any],
        language: str = "zh-CN",
        **kwargs,
    ) -> AsyncGenerator[AgentMessage, None]:
        """
        Generate natural language answer with streaming

        Args:
            question: User's question
            cube_query: Executed Cube Query
            result_data: Query results
            chart_config: Generated chart config
            language: Output language

        Yields:
            AgentMessage chunks with partial answer
        """
        logger.info(
            f"Generating answer (streaming) for question: {question[:100]}..."
        )

        try:
            prompt = self._get_prompt(
                question=question,
                query_metadata=query_metadata,
                result_data=result_data,
                chart_config=chart_config,
                language=language,
            )

            accumulated_content = ""
            async for chunk in self.llm.generate_stream(prompt, temperature=0.7):
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

            logger.info("Answer streaming completed")

        except Exception as e:
            logger.error(f"Answer streaming failed: {e}")
            fallback = self._get_fallback_answer(
                result_data=result_data, language=language
            )
            yield AgentMessage(
                agent_name=self.name,
                content=fallback,
                metadata={
                    "question": question,
                    "error": str(e),
                    "fallback": True,
                    "stream": True,
                },
            )

    def _get_fallback_answer(
        self, result_data: List[Dict], language: str = "zh-CN"
    ) -> str:
        """Generate simple fallback answer"""
        row_count = len(result_data)

        if language == "zh-CN":
            return f"查询成功完成，共找到 {row_count} 条记录。详细数据请查看上方的图表和表格。"
        else:
            return f"Query completed successfully with {row_count} records found. Please see the chart and table above for details."
