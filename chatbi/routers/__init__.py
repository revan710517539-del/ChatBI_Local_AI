"""
API router registration.

This module collects and exports all API routers for the application.
"""

from fastapi import APIRouter

# Import routers
from chatbi.domain.auth.router import router as AuthRouter
from chatbi.domain.chat import ChatRouter

from chatbi.domain.datasource import DatasourceRouter
from chatbi.domain.llm import LLMRouter
from chatbi.domain.mdl import MDLRouter
from chatbi.domain.ask import AskRouter
from chatbi.domain.ai_config import AIConfigRouter
from chatbi.domain.agent_builder import AgentBuilderRouter
from chatbi.domain.dashboard import DashboardRouter
from chatbi.routers.metrics import router as MetricsRouter

# Create main router
api_router = APIRouter()

# Include all routers
api_router.include_router(AuthRouter)  # Auth first - no prefix needed (already /api/v1/auth)
api_router.include_router(ChatRouter)

api_router.include_router(DatasourceRouter)
api_router.include_router(LLMRouter)
api_router.include_router(MDLRouter)
api_router.include_router(AskRouter)  # Ask endpoint for GenBI streaming
api_router.include_router(MetricsRouter)  # Metrics endpoint for Prometheus
api_router.include_router(AIConfigRouter)
api_router.include_router(AgentBuilderRouter)
api_router.include_router(DashboardRouter)

__all__ = ["api_router"]
