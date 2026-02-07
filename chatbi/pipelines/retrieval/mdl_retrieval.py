"""
MDL Retrieval Pipeline

Retrieves relevant MDL context from Qdrant for LLM query generation:

Pipeline Steps:
1. Generate embedding for user's question
2. Search Qdrant for similar MDL documents (models + columns)
3. Filter by project_id for isolation
4. Format results into LLM-friendly context

Usage:
    pipeline = MDLRetrievalPipeline(qdrant_manager, llm_provider)
    context = await pipeline.run(question, project_id, top_k=5)
"""

from typing import Dict, List, Optional
from uuid import UUID

from loguru import logger
from qdrant_client.models import FieldCondition, Filter, MatchValue

from chatbi.agent.llm.base_llm import BaseLLM
from chatbi.config import config
from chatbi.database.qdrant import AsyncQdrantManager


class MDLRetrievalPipeline:
    """Pipeline for retrieving MDL context from Qdrant"""

    def __init__(
        self,
        qdrant_manager: AsyncQdrantManager,
        llm_provider: BaseLLM,
        collection_name: Optional[str] = None,
    ):
        self.qdrant = qdrant_manager
        self.llm = llm_provider
        self.collection_name = collection_name or config.qdrant.collection_name

    async def run(
        self,
        question: str,
        project_id: UUID,
        top_k: int = 5,
        score_threshold: float = 0.7,
    ) -> str:
        """
        Retrieve relevant MDL context for a question

        Args:
            question: User's natural language question
            project_id: MDL project ID for isolation
            top_k: Number of top results to retrieve
            score_threshold: Minimum similarity score (0-1)

        Returns:
            Formatted context string for LLM prompt
        """
        logger.info(f"Retrieving MDL context for question: {question[:100]}...")

        try:
            # Step 1: Generate embedding for question
            query_embedding = await self._generate_embedding(question)
            if not query_embedding:
                logger.warning("Failed to generate query embedding, returning empty context")
                return ""

            # Step 2: Search Qdrant with project filter
            results = await self._search_mdl(
                query_embedding, project_id, top_k, score_threshold
            )

            # Step 3: Format results into context
            context = self._format_context(results)

            logger.info(
                f"Retrieved {len(results)} MDL documents (score >= {score_threshold})"
            )
            return context

        except Exception as e:
            logger.error(f"MDL retrieval failed: {e}")
            return ""

    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding vector for text using LLM provider"""
        try:
            # Use LLM's embedding method if available
            if hasattr(self.llm, "embed"):
                embedding = await self.llm.embed(text)
                return embedding

            # Fallback: Use OpenAI embedding API directly
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=config.llm.api_key,
                base_url=config.llm.base_url,
            )

            response = await client.embeddings.create(
                model="text-embedding-ada-002", input=text
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None

    async def _search_mdl(
        self,
        query_vector: List[float],
        project_id: UUID,
        top_k: int,
        score_threshold: float,
    ) -> List[Dict]:
        """Search Qdrant for similar MDL documents"""
        # Create project filter
        filter_condition = Filter(
            must=[
                FieldCondition(
                    key="project_id",
                    match=MatchValue(value=str(project_id)),
                )
            ]
        )

        # Search Qdrant
        results = await self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k * 2,  # Retrieve more, filter by score later
            filter_conditions=filter_condition,
        )

        # Filter by score threshold
        filtered_results = [r for r in results if r["score"] >= score_threshold]

        # Take top_k after filtering
        return filtered_results[:top_k]

    def _format_context(self, results: List[Dict]) -> str:
        """Format search results into LLM-friendly context"""
        if not results:
            return ""

        # Group results by model
        models_dict: Dict[str, Dict] = {}
        columns_list: List[Dict] = []

        for result in results:
            payload = result["payload"]
            doc_type = payload.get("type")
            score = result["score"]

            if doc_type == "model":
                model_name = payload.get("model_name")
                if model_name not in models_dict:
                    models_dict[model_name] = {
                        "name": model_name,
                        "display_name": payload.get("display_name", model_name),
                        "description": payload.get("description", ""),
                        "source_table": payload.get("source_table", ""),
                        "score": score,
                        "columns": [],
                    }

            elif doc_type == "column":
                columns_list.append(
                    {
                        "model_name": payload.get("model_name"),
                        "column_name": payload.get("column_name"),
                        "display_name": payload.get("display_name", ""),
                        "column_type": payload.get("column_type", ""),
                        "data_type": payload.get("data_type", ""),
                        "description": payload.get("description", ""),
                        "aggregation": payload.get("aggregation", ""),
                        "score": score,
                    }
                )

        # Attach columns to their models
        for column in columns_list:
            model_name = column["model_name"]
            if model_name not in models_dict:
                # Create model entry if not exists
                models_dict[model_name] = {
                    "name": model_name,
                    "display_name": model_name,
                    "description": "",
                    "source_table": "",
                    "score": column["score"],
                    "columns": [],
                }
            models_dict[model_name]["columns"].append(column)

        # Format as text
        context_parts = ["### Available Data Models ###\n"]

        for model_name, model_data in models_dict.items():
            context_parts.append(
                f"\n**Model: {model_data['display_name']}** (score: {model_data['score']:.2f})"
            )
            context_parts.append(f"- Name: {model_data['name']}")

            if model_data['description']:
                context_parts.append(f"- Description: {model_data['description']}")

            if model_data['source_table']:
                context_parts.append(f"- Source: {model_data['source_table']}")

            if model_data['columns']:
                context_parts.append("\n  **Columns:**")
                for col in model_data['columns']:
                    col_info = f"  - {col['display_name'] or col['column_name']} ({col['column_type']}, {col['data_type']})"
                    if col['aggregation']:
                        col_info += f" [agg: {col['aggregation']}]"
                    if col['description']:
                        col_info += f" - {col['description']}"
                    context_parts.append(col_info)

        context_parts.append("\n### End of Data Models ###")

        return "\n".join(context_parts)
