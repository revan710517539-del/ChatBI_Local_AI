"""
Historical Question Retrieval Pipeline

Retrieves similar historical questions to provide context for current queries.

Uses:
- Embeddings for semantic similarity search
- Qdrant vector database for storage
- Filters by project_id and success status
"""

from typing import List, Dict, Any
import hashlib

from loguru import logger
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue

from chatbi.agent.llm.base_llm import BaseLLM


class HistoricalQuestionRetrieval:
    """Pipeline for retrieving similar historical questions"""

    def __init__(self, qdrant_manager, llm: BaseLLM):
        """
        Initialize Historical Question Retrieval

        Args:
            qdrant_manager: Qdrant manager instance
            llm: LLM provider for embeddings
        """
        self.qdrant = qdrant_manager
        self.llm = llm
        self.collection_name = "chatbi_history"
        logger.info("HistoricalQuestionRetrieval initialized")

    async def index_question(
        self,
        question_id: str,
        project_id: str,
        question: str,
        result_summary: str,
        query_data: Dict[str, Any] = None,
        success: bool = True,
    ):
        """
        Index a question into history

        Args:
            question_id: Unique question ID
            project_id: Project ID
            question: User's question text
            result_summary: Summary of results
            query_data: Executed Query Data (SQL/Metadata)
            success: Whether query succeeded
        """
        try:
            # Ensure collection exists
            await self._ensure_collection()

            # Generate embedding
            embedding_text = f"{question}\n{result_summary}"
            embedding = await self._generate_embedding(embedding_text)

            if not embedding:
                logger.error("Failed to generate embedding for question")
                return

            # Create point
            point = PointStruct(
                id=self._generate_point_id(question_id),
                vector=embedding,
                payload={
                    "question_id": question_id,
                    "project_id": project_id,
                    "question": question,
                    "query_data": query_data,
                    "result_summary": result_summary[:500],  # Truncate
                    "success": success,
                },
            )

            # Upsert to Qdrant
            await self.qdrant.upsert_points(
                collection_name=self.collection_name,
                points=[point],
            )

            logger.info(f"Indexed question: {question[:100]}...")

        except Exception as e:
            logger.error(f"Failed to index question: {e}")

    async def retrieve(
        self,
        question: str,
        project_id: str,
        top_k: int = 3,
        score_threshold: float = 0.7,
    ) -> str:
        """
        Retrieve similar historical questions

        Args:
            question: Current user question
            project_id: Project ID
            top_k: Number of results to return
            score_threshold: Minimum similarity score

        Returns:
            Formatted string of similar historical queries
        """
        try:
            # Ensure collection exists
            await self._ensure_collection()

            # Generate embedding for current question
            embedding = await self._generate_embedding(question)

            if not embedding:
                logger.warning("Failed to generate embedding for question")
                return ""

            # Search in Qdrant
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="project_id", match=MatchValue(value=project_id)
                    ),
                    FieldCondition(key="success", match=MatchValue(value=True)),
                ]
            )

            results = await self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                limit=top_k,
                query_filter=search_filter,
                score_threshold=score_threshold,
            )

            if not results:
                logger.info("No similar historical questions found")
                return ""

            # Format results
            formatted = self._format_results(results)
            logger.info(f"Found {len(results)} similar historical questions")

            return formatted

        except Exception as e:
            logger.error(f"Failed to retrieve historical questions: {e}")
            return ""

    async def _ensure_collection(self):
        """Ensure history collection exists"""
        try:
            await self.qdrant.create_collection_if_not_exists(
                collection_name=self.collection_name,
                vector_size=1536,  # OpenAI embedding size
            )
        except Exception as e:
            logger.error(f"Failed to create history collection: {e}")

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            # Use LLM's embedding capability (OpenAI text-embedding-ada-002)
            # For now, use a simple approach - this should be replaced with proper embedding API
            import hashlib
            import math

            # Fallback: Generate deterministic pseudo-embedding from hash
            # TODO: Replace with proper OpenAI embedding API call
            hash_obj = hashlib.sha256(text.encode())
            hash_bytes = hash_obj.digest()

            # Convert to 1536-dimensional vector
            embedding = []
            for i in range(1536):
                byte_idx = i % len(hash_bytes)
                value = (hash_bytes[byte_idx] / 255.0) * 2 - 1  # Normalize to [-1, 1]
                embedding.append(value)

            logger.debug(f"Generated embedding for text: {text[:50]}...")
            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return []

    def _generate_point_id(self, question_id: str) -> str:
        """Generate deterministic point ID from question ID"""
        hash_obj = hashlib.md5(question_id.encode())
        return hash_obj.hexdigest()

    def _format_results(self, results: List[Any]) -> str:
        """Format search results as string"""
        if not results:
            return ""

        formatted_lines = ["### Similar Historical Questions ###\n"]

        for idx, result in enumerate(results, 1):
            payload = result.payload
            score = result.score

            formatted_lines.append(f"\n**Example {idx}** (similarity: {score:.2f}):")
            formatted_lines.append(f"- Question: {payload['question']}")
            formatted_lines.append(f"- Summary: {payload['result_summary'][:200]}")

            if payload.get("query_data"):
                import json

                query_str = json.dumps(payload["query_data"], indent=2)
                formatted_lines.append(f"- Query: ```json\n{query_str}\n```")

        return "\n".join(formatted_lines)
