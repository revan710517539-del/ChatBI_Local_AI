"""
Metrics API Router

Exposes Prometheus metrics endpoint.
"""

from fastapi import APIRouter, Response
from loguru import logger

from chatbi.observability.metrics import get_metrics_collector, CONTENT_TYPE_LATEST

router = APIRouter(tags=["Metrics"])


@router.get("/metrics")
async def get_metrics():
    """
    Get Prometheus metrics
    
    Returns:
        Prometheus metrics in text format
    
    Example:
        ```
        curl http://localhost:8000/metrics
        ```
    """
    logger.debug("Metrics endpoint called")
    
    collector = get_metrics_collector()
    metrics_data = collector.get_metrics()
    
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST,
    )


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        Simple health status
    """
    return {"status": "healthy"}
