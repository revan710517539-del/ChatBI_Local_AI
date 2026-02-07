"""
Qdrant Vector Database Connection Manager

Manages Qdrant client connections for vector storage and retrieval:
- Connection pooling and lifecycle management
- Collection creation and management
- Health checks
"""

from typing import Dict, List, Optional

from loguru import logger
from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from chatbi.config import config


class QdrantManager:
    """Qdrant connection manager (synchronous)"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        grpc_port: int = 6334,
        prefer_grpc: bool = True,
    ):
        self.host = host
        self.port = port
        self.grpc_port = grpc_port
        self.prefer_grpc = prefer_grpc
        self._client: Optional[QdrantClient] = None

    @property
    def client(self) -> QdrantClient:
        """Get or create Qdrant client"""
        if self._client is None:
            self._client = QdrantClient(
                host=self.host,
                port=self.port,
                grpc_port=self.grpc_port,
                prefer_grpc=self.prefer_grpc,
            )
            logger.info(f"Connected to Qdrant at {self.host}:{self.port}")
        return self._client

    def close(self):
        """Close Qdrant connection"""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Qdrant connection closed")

    def health_check(self) -> bool:
        """Check Qdrant health"""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

    def create_collection_if_not_exists(
        self,
        collection_name: str,
        vector_size: int = 1536,
        distance: Distance = Distance.COSINE,
    ) -> bool:
        """Create collection if it doesn't exist"""
        try:
            collections = self.client.get_collections().collections
            if any(c.name == collection_name for c in collections):
                logger.info(f"Collection '{collection_name}' already exists")
                return True

            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=distance),
            )
            logger.info(
                f"Created collection '{collection_name}' (size={vector_size}, distance={distance})"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create collection '{collection_name}': {e}")
            return False

    def upsert_points(
        self,
        collection_name: str,
        points: List[PointStruct],
    ) -> bool:
        """Insert or update points in collection"""
        try:
            self.client.upsert(collection_name=collection_name, points=points)
            logger.info(f"Upserted {len(points)} points to '{collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to upsert points to '{collection_name}': {e}")
            return False

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        filter_conditions: Optional[Filter] = None,
    ) -> List[Dict]:
        """Search for similar vectors"""
        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=filter_conditions,
            )
            logger.debug(
                f"Found {len(results)} results in '{collection_name}' (limit={limit})"
            )
            return [
                {
                    "id": r.id,
                    "score": r.score,
                    "payload": r.payload,
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Failed to search in '{collection_name}': {e}")
            return []

    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection"""
        try:
            self.client.delete_collection(collection_name=collection_name)
            logger.info(f"Deleted collection '{collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection '{collection_name}': {e}")
            return False

    def delete_points_by_filter(
        self, collection_name: str, filter_conditions: Filter
    ) -> bool:
        """Delete points matching filter"""
        try:
            self.client.delete(
                collection_name=collection_name, points_selector=filter_conditions
            )
            logger.info(f"Deleted points from '{collection_name}' matching filter")
            return True
        except Exception as e:
            logger.error(f"Failed to delete points from '{collection_name}': {e}")
            return False


class AsyncQdrantManager:
    """Qdrant connection manager (asynchronous)"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        grpc_port: int = 6334,
        prefer_grpc: bool = True,
    ):
        self.host = host
        self.port = port
        self.grpc_port = grpc_port
        self.prefer_grpc = prefer_grpc
        self._client: Optional[AsyncQdrantClient] = None

    @property
    def client(self) -> AsyncQdrantClient:
        """Get or create async Qdrant client"""
        if self._client is None:
            self._client = AsyncQdrantClient(
                host=self.host,
                port=self.port,
                grpc_port=self.grpc_port,
                prefer_grpc=self.prefer_grpc,
            )
            logger.info(f"Connected to Qdrant (async) at {self.host}:{self.port}")
        return self._client

    async def close(self):
        """Close Qdrant connection"""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Qdrant async connection closed")

    async def health_check(self) -> bool:
        """Check Qdrant health"""
        try:
            await self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

    async def create_collection_if_not_exists(
        self,
        collection_name: str,
        vector_size: int = 1536,
        distance: Distance = Distance.COSINE,
    ) -> bool:
        """Create collection if it doesn't exist"""
        try:
            collections = await self.client.get_collections()
            if any(c.name == collection_name for c in collections.collections):
                logger.info(f"Collection '{collection_name}' already exists")
                return True

            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=distance),
            )
            logger.info(
                f"Created collection '{collection_name}' (size={vector_size}, distance={distance})"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create collection '{collection_name}': {e}")
            return False

    async def upsert_points(
        self,
        collection_name: str,
        points: List[PointStruct],
    ) -> bool:
        """Insert or update points in collection"""
        try:
            await self.client.upsert(collection_name=collection_name, points=points)
            logger.info(f"Upserted {len(points)} points to '{collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to upsert points to '{collection_name}': {e}")
            return False

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        filter_conditions: Optional[Filter] = None,
    ) -> List[Dict]:
        """Search for similar vectors"""
        try:
            results = await self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=filter_conditions,
            )
            logger.debug(
                f"Found {len(results)} results in '{collection_name}' (limit={limit})"
            )
            return [
                {
                    "id": r.id,
                    "score": r.score,
                    "payload": r.payload,
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Failed to search in '{collection_name}': {e}")
            return []

    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection"""
        try:
            await self.client.delete_collection(collection_name=collection_name)
            logger.info(f"Deleted collection '{collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection '{collection_name}': {e}")
            return False

    async def delete_points_by_filter(
        self, collection_name: str, filter_conditions: Filter
    ) -> bool:
        """Delete points matching filter"""
        try:
            await self.client.delete(
                collection_name=collection_name, points_selector=filter_conditions
            )
            logger.info(f"Deleted points from '{collection_name}' matching filter")
            return True
        except Exception as e:
            logger.error(f"Failed to delete points from '{collection_name}': {e}")
            return False


# Global instance
_qdrant_manager: Optional[QdrantManager] = None
_async_qdrant_manager: Optional[AsyncQdrantManager] = None


def get_qdrant_manager() -> QdrantManager:
    """Get global Qdrant manager instance"""
    global _qdrant_manager
    if _qdrant_manager is None:
        qdrant_config = config.qdrant
        _qdrant_manager = QdrantManager(
            host=qdrant_config.host,
            port=qdrant_config.port,
            grpc_port=qdrant_config.grpc_port,
            prefer_grpc=qdrant_config.prefer_grpc,
        )
    return _qdrant_manager


def get_async_qdrant_manager() -> AsyncQdrantManager:
    """Get global async Qdrant manager instance"""
    global _async_qdrant_manager
    if _async_qdrant_manager is None:
        qdrant_config = config.qdrant
        _async_qdrant_manager = AsyncQdrantManager(
            host=qdrant_config.host,
            port=qdrant_config.port,
            grpc_port=qdrant_config.grpc_port,
            prefer_grpc=qdrant_config.prefer_grpc,
        )
    return _async_qdrant_manager


def close_qdrant_connections():
    """Close all Qdrant connections"""
    global _qdrant_manager, _async_qdrant_manager
    if _qdrant_manager:
        _qdrant_manager.close()
        _qdrant_manager = None
    if _async_qdrant_manager:
        # Note: async close needs to be awaited in async context
        logger.warning("Async Qdrant manager should be closed in async context")
        _async_qdrant_manager = None
