"""
Chart Generation Agent

Generates chart configurations from query results.

Supports multiple chart types:
- bar: Categorical comparisons
- line: Trends over time
- pie: Proportions/percentages
- table: Raw data display
- area: Trends with emphasis on volume
- scatter: Correlation analysis

Output format compatible with AVA (Ant Visualization Advisor) and Vega-Lite.
"""

import json
from typing import Dict, Any, List, Optional

from loguru import logger

from chatbi.agent.agent_base import AgentBase
from chatbi.agent.agent_message import AgentMessage


class ChartGenerationAgent(AgentBase):
    """Agent for generating chart configurations"""

    def __init__(self, llm_provider):
        super().__init__(name="ChartGenerationAgent", llm_provider=llm_provider)

    def _get_prompt(
        self,
        question: str,
        query_metadata: Dict[str, Any],
        result_data: List[Dict],
        result_summary: str = "",
    ) -> str:
        """Generate chart generation prompt"""
        return f"""You are a data visualization expert. Generate the BEST chart configuration for the given data.

### USER'S QUESTION ###
{question}

### QUERY CONTEXT ###
```json
{json.dumps(query_metadata, indent=2)}
```

### QUERY RESULT (first 5 rows) ###
```json
{json.dumps(result_data[:5], indent=2)}
```

### RESULT SUMMARY ###
Total rows: {len(result_data)}
{result_summary}

### CHART TYPE SELECTION RULES ###

**bar**: Use for categorical comparisons
- Example: Sales by product, revenue by region
- Requirements: 1+ categorical dimension, 1+ measure
- Best for: <20 categories

**line**: Use for trends over time
- Example: Sales over months, user growth
- Requirements: 1 time dimension, 1+ measure
- Best for: Time series data

**pie**: Use for proportions/percentages
- Example: Market share, category distribution
- Requirements: 1 categorical dimension, 1 measure
- Best for: <7 categories, sum = 100% or meaningful total

**area**: Use for trends with volume emphasis
- Example: Cumulative sales, stacked categories over time
- Requirements: 1 time dimension, 1+ measure
- Best for: Emphasizing magnitude/volume

**scatter**: Use for correlation analysis
- Example: Sales vs profit margin
- Requirements: 2+ measures
- Best for: Finding relationships between metrics

**table**: Use as fallback
- When no clear pattern
- When user asks for "detailed data" or "list"
- When data is too complex for charts

### YOUR TASK ###
1. Analyze the data structure (columns, types, cardinality)
2. Choose the MOST APPROPRIATE chart type based on rules above
3. Generate chart configuration in the format below

### OUTPUT FORMAT ###
Return a JSON object with:
- chartType: string (bar, line, pie, area, scatter, table)
- title: string (descriptive title)
- description: string (what the chart shows)
- spec: object (chart specification)
  - For bar/line/area:
    {{
      "xField": "column_name",
      "yField": "column_name",
      "seriesField": "column_name" (optional, for grouped charts)
    }}
  - For pie:
    {{
      "angleField": "value_column",
      "colorField": "category_column"
    }}
  - For scatter:
    {{
      "xField": "column_name",
      "yField": "column_name",
      "sizeField": "column_name" (optional),
      "colorField": "column_name" (optional)
    }}
  - For table:
    {{
      "columns": ["col1", "col2", ...]
    }}

Example:
{{
  "chartType": "bar",
  "title": "Top 5 Products by Sales",
  "description": "Shows the 5 products with highest total sales in 2023",
  "spec": {{
    "xField": "Products.name",
    "yField": "Orders.totalAmount",
    "label": {{
      "position": "top",
      "style": {{
        "fill": "#000000",
        "opacity": 0.6
      }}
    }}
  }}
}}

Return ONLY the JSON object, no additional text.
"""

    async def replay(
        self,
        question: str,
        query_metadata: Dict[str, Any],
        result_data: List[Dict],
        result_summary: str = "",
        **kwargs,
    ) -> AgentMessage:
        """
        Generate chart configuration

        Args:
            question: User's question
            query_metadata: Executed Query Metadata
            result_data: Query result data
            result_summary: Optional summary of results

        Returns:
            AgentMessage with chart config
        """
        logger.info(f"Generating chart for question: {question[:100]}...")

        try:
            # Auto-detect simple cases without LLM
            auto_config = self._auto_detect_chart(
                query_metadata=query_metadata,
                result_data=result_data,
                question=question,
            )

            if auto_config and not self._should_use_llm(question):
                logger.info(f"Auto-detected chart type: {auto_config['chartType']}")
                return AgentMessage(
                    agent_name=self.name,
                    content=json.dumps(auto_config),
                    metadata={
                        "question": question,
                        "chart_config": auto_config,
                        "method": "auto_detect",
                    },
                )

            # Use LLM for complex cases
            prompt = self._get_prompt(
                question=question,
                query_metadata=query_metadata,
                result_data=result_data,
                result_summary=result_summary,
            )

            response = await self.llm.generate(prompt, temperature=0.2)
            chart_config = self._extract_json(response)

            if not chart_config or "chartType" not in chart_config:
                # Fallback to auto-detect
                logger.warning("LLM failed to generate chart, using auto-detect")
                chart_config = auto_config or self._get_fallback_config(result_data)

            logger.info(f"Generated chart: {chart_config['chartType']}")

            return AgentMessage(
                agent_name=self.name,
                content=json.dumps(chart_config),
                metadata={
                    "question": question,
                    "chart_config": chart_config,
                    "method": "llm",
                },
            )

        except Exception as e:
            logger.error(f"Chart generation failed: {e}")
            # Return table as fallback
            fallback = self._get_fallback_config(result_data)
            return AgentMessage(
                agent_name=self.name,
                content=json.dumps(fallback),
                metadata={
                    "question": question,
                    "chart_config": fallback,
                    "error": str(e),
                    "method": "fallback",
                },
            )

    def _auto_detect_chart(
        self,
        query_metadata: Dict[str, Any],
        result_data: List[Dict],
        question: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Auto-detect chart type based on data structure

        Args:
            query_metadata: Query Metadata
            result_data: Result data
            question: User question

        Returns:
            Chart config or None if can't determine
        """
        if not result_data:
            return None

        measures = query_metadata.get("measures", [])
        dimensions = query_metadata.get("dimensions", [])
        time_dimensions = query_metadata.get("timeDimensions", [])

        # Get column names from first row
        columns = list(result_data[0].keys())
        row_count = len(result_data)

        # Time series with time dimension → line chart
        if time_dimensions and len(time_dimensions) > 0:
            time_col = columns[0]  # Usually first column
            value_col = columns[1] if len(columns) > 1 else columns[0]

            return {
                "chartType": "line",
                "title": self._generate_title(question, "line"),
                "description": f"Trend analysis with {row_count} data points",
                "spec": {
                    "xField": time_col,
                    "yField": value_col,
                    "smooth": True,
                },
            }

        # Single measure + single dimension, small cardinality → bar chart
        if (
            len(measures) == 1
            and len(dimensions) == 1
            and row_count <= 20
            and row_count >= 2
        ):
            dim_col = columns[0]
            measure_col = columns[1] if len(columns) > 1 else columns[0]

            # Check if pie is more appropriate (proportions)
            if row_count <= 7 and "percentage" not in question.lower():
                return {
                    "chartType": "bar",
                    "title": self._generate_title(question, "bar"),
                    "description": f"Comparison across {row_count} categories",
                    "spec": {
                        "xField": dim_col,
                        "yField": measure_col,
                        "label": {"position": "top"},
                    },
                }

        # Pie chart keywords
        if any(
            kw in question.lower()
            for kw in ["proportion", "percentage", "share", "distribution", "占比", "比例"]
        ):
            if len(dimensions) == 1 and len(measures) == 1 and row_count <= 7:
                dim_col = columns[0]
                measure_col = columns[1] if len(columns) > 1 else columns[0]

                return {
                    "chartType": "pie",
                    "title": self._generate_title(question, "pie"),
                    "description": f"Distribution across {row_count} categories",
                    "spec": {
                        "angleField": measure_col,
                        "colorField": dim_col,
                    },
                }

        # Too many rows or complex structure → table
        if row_count > 50 or len(columns) > 5:
            return {
                "chartType": "table",
                "title": self._generate_title(question, "table"),
                "description": f"Detailed data view with {row_count} rows",
                "spec": {
                    "columns": columns,
                },
            }

        return None

    def _should_use_llm(self, question: str) -> bool:
        """Determine if LLM is needed for chart selection"""
        # Use LLM for complex questions
        complex_keywords = [
            "compare",
            "trend",
            "correlation",
            "relationship",
            "analyze",
            "对比",
            "趋势",
            "相关",
            "关系",
            "分析",
        ]

        return any(kw in question.lower() for kw in complex_keywords)

    def _generate_title(self, question: str, chart_type: str) -> str:
        """Generate simple title from question"""
        # Take first 50 chars of question
        title = question[:50]
        if len(question) > 50:
            title += "..."
        return title

    def _get_fallback_config(self, result_data: List[Dict]) -> Dict[str, Any]:
        """Get fallback table configuration"""
        columns = list(result_data[0].keys()) if result_data else []

        return {
            "chartType": "table",
            "title": "Query Results",
            "description": f"Data table with {len(result_data)} rows",
            "spec": {
                "columns": columns,
            },
        }

    def _extract_json(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try markdown code block
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            else:
                # Find JSON object
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    return json.loads(json_str)

        logger.error(f"Could not extract JSON from response: {response[:200]}")
        return {}
