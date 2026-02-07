"""
LLM router

This module provides FastAPI routes for handling chat functionality with standardized responses.
"""

from fastapi import APIRouter, status

from chatbi.domain.llm.dtos import CreateCompletionsDTO
from chatbi.domain.llm.service import LLMService
from chatbi.middleware.standard_response import StandardResponse

# Create router instance


router = APIRouter(
    prefix="/llm",
    tags=["LLM"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Resource not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "An unexpected error occurred", "code": 500}
                }
            },
        },
    },
)


# proxy openai completions api
@router.post("/completions")
async def completions(body: CreateCompletionsDTO):
    llm_service = LLMService()

    result = llm_service.completions(body)
    return result
