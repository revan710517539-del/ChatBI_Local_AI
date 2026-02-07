"""
Ask Router - REST API endpoints for question answering

Provides SSE streaming endpoint for real-time GenBI responses.
"""

import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

from chatbi.domain.ask.dtos import AskRequestDTO
from chatbi.dependencies import AsyncQdrantDep, get_current_user
from chatbi.agent.llm.openai import OpenaiModel
from chatbi.pipelines.ask.ask_pipeline import AskPipeline


router = APIRouter(prefix="/api/v1/ask", tags=["Ask"])


@router.post(
    "",
    response_class=StreamingResponse,
    summary="Ask a question with streaming response",
    description="""
    Ask a natural language question about your data and get a streaming response.

    The response is a Server-Sent Events (SSE) stream with the following event types:
    - `intent`: User intent classification (query/greeting/help/clarification)
    - `mdl_context`: Retrieved MDL semantic layer context
    - `reasoning`: Step-by-step reasoning plan (streamed)
    - `cube_query`: Generated Cube.js Query JSON
    - `validation`: Query validation result (valid/invalid)
    - `correction`: Query correction result (if needed)
    - `result`: Query execution result with data
    - `answer`: Natural language answer (streamed)
    - `error`: Error message (if any)
    - `done`: Pipeline completed

    Example:
    ```
    event: reasoning
    data: {"type": "reasoning", "content": "Step 1: Understanding the question...", "stream": true}

    event: cube_query
    data: {"type": "cube_query", "content": {"measures": ["Orders.totalAmount"], ...}}

    event: result
    data: {"type": "result", "content": [...], "row_count": 10}

    event: done
    data: {"type": "done", "total_time_ms": 5000}
    ```
    """,
)
async def ask_question(
    request: AskRequestDTO,
    qdrant: AsyncQdrantDep,
    current_user=Depends(get_current_user),
) -> StreamingResponse:
    """
    Ask a question with streaming response

    Args:
        request: Question request with project_id, question, etc.
        qdrant: Qdrant manager for MDL retrieval
        current_user: Current authenticated user

    Returns:
        StreamingResponse with Server-Sent Events
    """
    logger.info(
        f"Ask request from user {current_user.user_id}: {request.question[:100]}"
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events"""
        try:
            # Initialize LLM and pipeline
            llm = OpenaiModel()
            pipeline = AskPipeline(
                llm=llm, qdrant_manager=qdrant
            )

            # Run pipeline with streaming
            async for event in pipeline.run(
                question=request.question,
                project_id=request.project_id,
                session_id=request.session_id,
                user_id=str(current_user.user_id),
                language=request.language,
                max_correction_attempts=request.max_correction_attempts,
            ):
                # Format as SSE
                event_type = event.get("type", "data")
                event_data = json.dumps(event, ensure_ascii=False)

                yield f"event: {event_type}\n"
                yield f"data: {event_data}\n\n"

        except Exception as e:
            logger.error(f"Ask pipeline failed: {e}", exc_info=True)

            # Send error event
            error_event = {
                "type": "error",
                "content": str(e),
                "error_type": "pipeline_error",
            }
            yield f"event: error\n"
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

            # Send done event
            done_event = {"type": "done"}
            yield f"event: done\n"
            yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get(
    "/health",
    summary="Check Ask service health",
    description="Health check for Ask service and dependencies",
)
async def health_check(qdrant: AsyncQdrantDep) -> dict:
    """
    Health check endpoint

    Returns:
        Health status of Ask service
    """
    try:
        # Check Qdrant connection
        qdrant_healthy = await qdrant.health_check()

        if qdrant_healthy:
            return {
                "status": "ok",
                "qdrant": "ok",
            }
        else:
            return {
                "status": "degraded",
                "qdrant": "ok" if qdrant_healthy else "error",
            }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


AskRouter = router
