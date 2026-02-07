"""
Ask DTOs - Request/Response schemas for question answering
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class AskRequestDTO(BaseModel):
    """Request for asking a question"""

    question: str = Field(..., description="User's natural language question")
    project_id: str = Field(..., description="MDL project ID")
    session_id: Optional[str] = Field(None, description="Session ID for context")
    language: Literal["zh-CN", "en-US"] = Field(
        "zh-CN", description="Response language"
    )
    max_correction_attempts: int = Field(
        2, ge=0, le=5, description="Max query correction retries"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "question": "过去一个月的销售额是多少？",
                    "project_id": "550e8400-e29b-41d4-a716-446655440000",
                    "session_id": "660e8400-e29b-41d4-a716-446655440000",
                    "language": "zh-CN",
                    "max_correction_attempts": 2,
                }
            ]
        }
    }


class AskEventDTO(BaseModel):
    """Server-Sent Event for streaming response"""

    event: str = Field(..., description="Event type")
    data: dict = Field(..., description="Event data")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "event": "reasoning",
                    "data": {"content": "Step 1: Understanding the question..."},
                }
            ]
        }
    }
