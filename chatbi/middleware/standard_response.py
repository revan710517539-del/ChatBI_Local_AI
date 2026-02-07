import hashlib
import json
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

from chatbi.config import get_config

config = get_config()

# Generic type for the data field in StandardResponse
T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    """
    Standardized response model for all API endpoints.

    This model provides a consistent structure for all API responses with:
    - A status field indicating success/error
    - A message field for human-readable information
    - A data field for the actual response data (generic)
    - A metadata field for additional information like pagination, timing, etc.
    - An errors field for detailed error information when applicable
    """

    status: str = "success"
    message: str = "Operation completed successfully"
    data: Optional[T] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    errors: Optional[list[dict[str, Any]]] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Data retrieved successfully",
                "data": {"id": "abc123", "name": "Example"},
                "metadata": {"page": 1, "page_size": 10, "total": 42},
                "timestamp": "2025-05-16T08:00:00.000000",
            }
        }


class StandardResponseMiddleware(BaseHTTPMiddleware):
    """
    Middleware to standardize API responses across the application.

    This middleware:
    1. Adds standard headers to all responses
    2. Calculates and adds ETag headers for cacheable responses
    3. Formats error responses consistently
    4. Adds API version information
    5. Adds pagination links when appropriate
    """

    def __init__(
        self,
        app,
        api_version: str = "1.0.0",
        include_etag: bool = True,
        include_response_time: bool = True,
    ):
        super().__init__(app)
        self.api_version = api_version
        self.include_etag = include_etag
        self.include_response_time = include_response_time

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Process the request through the application
        response = await call_next(request)

        # Skip middleware for non-API routes (static files, etc.)
        if not request.url.path.startswith("/api"):
            return response

        # Add standard headers to all API responses
        response.headers["X-API-Version"] = self.api_version

        # Add response time header if enabled
        if self.include_response_time:
            process_time = time.time() - start_time
            response.headers["X-Response-Time"] = f"{process_time:.4f}s"

        # Add request ID header for tracking
        if "X-Request-ID" not in response.headers:
            response.headers["X-Request-ID"] = (
                request.state.request_id
                if hasattr(request.state, "request_id")
                else "unknown"
            )

        # Add ETag for GET requests with JSON responses for conditional requests
        if (
            self.include_etag
            and request.method == "GET"
            and isinstance(response, JSONResponse)
        ):
            try:
                # Try to get the body to create an ETag
                response_body = b""

                # For streaming responses, we can't calculate an ETag
                if hasattr(response, "body"):
                    response_body = response.body

                if response_body:
                    etag = hashlib.md5(response_body).hexdigest()
                    response.headers["ETag"] = f'W/"{etag}"'

                    # Check If-None-Match header for conditional requests
                    if_none_match = request.headers.get("if-none-match")
                    if if_none_match and if_none_match == response.headers["ETag"]:
                        return Response(status_code=304, headers=response.headers)
            except Exception:
                # If we can't calculate an ETag, just skip it
                pass

        return response


def add_pagination_headers(
    response: Response,
    request: Request,
    total_count: int,
    page_size: int,
    current_page: int,
    total_pages: Optional[int] = None,
) -> Response:
    """
    Add pagination headers to a response.

    Args:
        response: The response to add headers to
        request: The original request
        total_count: Total number of items
        page_size: Number of items per page
        current_page: Current page number
        total_pages: Total number of pages (calculated if not provided)

    Returns:
        Response with pagination headers added
    """
    # Calculate total pages if not provided
    if total_pages is None:
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 0

    # Add pagination metadata headers
    response.headers["X-Total-Count"] = str(total_count)
    response.headers["X-Page-Size"] = str(page_size)
    response.headers["X-Current-Page"] = str(current_page)
    response.headers["X-Total-Pages"] = str(total_pages)

    # Generate pagination links
    base_url = str(request.url).split("?")[0]
    query_params = dict(request.query_params)

    links = []

    # First page
    first_params = query_params.copy()
    first_params["page"] = "1"
    first_page_url = (
        f"{base_url}?{'&'.join(f'{k}={v}' for k, v in first_params.items())}"
    )
    links.append(f'<{first_page_url}>; rel="first"')

    # Last page
    last_params = query_params.copy()
    last_params["page"] = str(total_pages)
    last_page_url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in last_params.items())}"
    links.append(f'<{last_page_url}>; rel="last"')

    # Previous page
    if current_page > 1:
        prev_params = query_params.copy()
        prev_params["page"] = str(current_page - 1)
        prev_page_url = (
            f"{base_url}?{'&'.join(f'{k}={v}' for k, v in prev_params.items())}"
        )
        links.append(f'<{prev_page_url}>; rel="prev"')

    # Next page
    if current_page < total_pages:
        next_params = query_params.copy()
        next_params["page"] = str(current_page + 1)
        next_page_url = (
            f"{base_url}?{'&'.join(f'{k}={v}' for k, v in next_params.items())}"
        )
        links.append(f'<{next_page_url}>; rel="next"')

    # Add Link header with all pagination links
    if links:
        response.headers["Link"] = ", ".join(links)

    return response


def add_hateoas_links(
    response_data: dict, resource_type: str, resource_id: str | None = None
) -> dict:
    """
    Add HATEOAS links to a response dictionary.

    Args:
        response_data: Response data dictionary to add links to
        resource_type: Type of resource (e.g., "users", "products")
        resource_id: Optional ID of the specific resource

    Returns:
        Dictionary with added "_links" field containing HATEOAS links
    """
    base_url = f"/api/v1/{resource_type}"

    links = {
        "self": {"href": f"{base_url}/{resource_id}" if resource_id else base_url},
        "collection": {"href": base_url},
    }

    # Add specific links based on resource type
    if resource_type == "chat":
        if resource_id:
            links["conversations"] = {"href": f"{base_url}/{resource_id}/conversations"}
            links["visualizations"] = {
                "href": f"{base_url}/{resource_id}/visualizations"
            }

    elif resource_type == "datasources":
        if resource_id:
            links["queries"] = {"href": f"{base_url}/{resource_id}/queries"}
            links["schema"] = {"href": f"{base_url}/{resource_id}/schema"}

    # Add documentation link
    links["docs"] = {"href": "/docs"}

    # Add _links to the response data (careful not to overwrite existing data)
    if isinstance(response_data, dict):
        if "_links" not in response_data:
            response_data["_links"] = links

    return response_data
