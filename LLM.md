# ChatBI Copilot Instructions

## Project Overview
ChatBI is a full-stack BI analytics system that uses LLM agents to convert natural language into SQL queries and visualizations. Architecture: Python/FastAPI backend with TypeScript/React (Ant Design X) frontend, PostgreSQL + DuckDB databases, multi-agent LLM system.

## Architecture Patterns

### Domain-Driven Design (DDD)
All business logic follows strict DDD organization in `chatbi/domain/`:
- **models.py**: Pure domain logic (no DB/API coupling)
- **entities.py**: SQLAlchemy ORM models with domain model conversion methods
- **dtos.py**: Pydantic models for API request/response
- **repository.py**: Data access layer (both sync/async)
- **service.py**: Business logic orchestration
- **router.py**: FastAPI endpoints

Example import pattern:
```python
from chatbi.domain import ChatSession, Message  # Common imports
from chatbi.domain.chat.entities import ChatHistory  # Specific access
```

### Multi-Agent System
Three specialized agents in `chatbi/agent/`:
- **SchemaAgent**: Analyzes database schemas and generates table descriptions
- **SqlAgent**: Converts natural language to SQL using LLM prompts
- **VisualizeAgent**: Generates chart specifications from query results

Each agent uses `AgentMessage` for structured communication and inherits from `AgentBase`.

### Database Architecture
**Multi-database adapter pattern** in `chatbi/database/drivers/`:
- Factory pattern (`factory.py`) with connection pooling (max 50 connections, 10/database)
- Adapters: DuckDB, PostgreSQL, MySQL, SQLite via `DatabaseAdapter` base class
- Connection lifecycle: `ConnectionManager` handles health checks, retries, and cleanup
- All connections go through `connection_manager.py` - NEVER create direct connections

**Two databases in use**:
- **PostgreSQL**: Application state, chat sessions, datasource configs
- **DuckDB**: Analytics queries and data analysis (embedded)

### Dependency Injection
Centralized DI system in `chatbi/dependencies.py`:
- `PostgresSessionDep`: Synchronous session for PostgreSQL
- `AsyncSessionDep`: Async session for PostgreSQL  
- `RepositoryDependency[T]`: Generic repo provider that auto-detects sync/async

```python
# Example: Define dependency once, use everywhere
ChatRepoDep = RepositoryDependency(ChatRepository)

@router.get("/sessions")
async def get_sessions(repo: ChatRepository = Depends(ChatRepoDep)):
    return await repo.get_all()
```

### Transaction Management
Use `@transactional` decorator from `chatbi.dependencies` for database operations:
```python
@transactional
async def update_session(self, session_id: UUID, data: dict):
    # Auto-commits on success, rolls back on error
    pass
```

### Caching System
Abstract cache interface (`chatbi/cache/base.py`) with implementations:
- `MemoryCache`: In-memory for dev/testing
- `RedisCache`: Production caching
- Decorator `@requires_cache(required_fields=["sql", "schema"])` validates cache state before execution

## Development Workflows

### Setup & Running
```bash
# Install dependencies (uses uv for Python, pnpm for Node)
make install          # or: just install

# Start infrastructure (Postgres, Redis, Cube.js)
make docker up        # or: just docker up

# Development servers
make dev-server       # Python FastAPI (port 8000)
make dev-client       # React dev server

# Update client API types from OpenAPI spec
make gen-api          # or: just gen-api
```

### Database Migrations
Uses Alembic - see `chatbi/migrations/README.md`:
```bash
# Create migration after model changes
uv run python -m chatbi.migrations.manage_migrations create "description"

# Apply migrations
uv run python -m chatbi.migrations.manage_migrations upgrade

# Check status
uv run python -m chatbi.migrations.manage_migrations status
```

### Testing & Linting
```bash
make test             # Run pytest tests
make lint             # Check formatting (ruff)
make format           # Auto-fix formatting (ruff + taplo)
```

## Configuration

### Environment Variables (`.env`)
Required variables from `.env.example`:
- `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`: LLM provider config (OpenAI/Tongyi/DeepSeek compatible)
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASS`: PostgreSQL connection
- `CUBE_SERVICE_API`: Cube.js API endpoint (default: http://localhost:4000)

Configuration loaded via `chatbi.config.ConfigModel` with Pydantic validation.

## Critical Implementation Details

### Middleware Stack
Applied in `chatbi/main.py`:
1. `RequestLoggerMiddleware`: Request ID generation and logging
2. `StandardResponseMiddleware`: Wraps all responses in consistent format
3. Error handlers via `add_error_handlers()`: Converts exceptions to standardized error responses
4. CORS: Configured for localhost:8001 (client)

### Repository Pattern
All DB access goes through repositories - NEVER query SQLAlchemy models directly in services:
```python
# ✅ Good
sessions = await chat_repository.get_by_user_id(user_id)

# ❌ Bad
sessions = session.query(ChatSession).filter_by(user_id=user_id).all()
```

### Logging
Uses Loguru with request ID tracking:
```python
from loguru import logger
logger.info(f"Processing session {session_id}")  # Auto-includes request ID
```
Logs stored in `runs/run.log` (rotated weekly).

### Frontend Integration
Client: `web/` - Umi.js + Ant Design X + AVA visualization
- API types auto-generated via `make gen-api` from FastAPI OpenAPI spec
- Uses `openapi-fetch` for type-safe API calls

## Project-Specific Conventions

- **Python version**: 3.11+ required (uses `uv` for dependency management, NOT pip)
- **Node.js version**: 18+ required (uses native fetch)
- **Import style**: Absolute imports from `chatbi.` root, re-exported via `domain/__init__.py`
- **Async by default**: New endpoints should be async unless DB operations are purely synchronous
- **Type hints**: All functions must have complete type annotations
- **Error handling**: Raise domain-specific exceptions from `chatbi.exceptions`, middleware converts to HTTP responses

## Common Tasks

### Adding a New Domain
1. Create `domain/<name>/` with `models.py`, `entities.py`, `dtos.py`, `repository.py`, `service.py`, `router.py`
2. Export key classes in `domain/<name>/__init__.py`
3. Re-export in `domain/__init__.py`
4. Register router in `routers/__init__.py`
5. Create migration: `uv run python -m chatbi.migrations.manage_migrations create "add <name> tables"`

### Adding Database Support
1. Create adapter in `database/drivers/<db>_adapter.py` extending `DatabaseAdapter`
2. Add `DatabaseType` enum value in `domain/datasource/models.py`
3. Register in `database/drivers/factory.py`'s `_adapter_registry`
4. Implement required methods: `connect()`, `disconnect()`, `execute_query()`, `get_tables()`, `get_schema()`

### Adding an LLM Agent
1. Create agent in `chatbi/agent/<name>_agent.py`
2. Inherit from `AgentBase`, implement `replay(**kwargs) -> AgentMessage`
3. Add prompt templates in `agent/prompts/`
4. Integrate in service layer (typically `domain/chat/service.py`)

## Integration Points
- **Cube.js**: OLAP layer for analytics queries (optional, config in `docker/cube/`)
- **Redis**: Production caching (optional, falls back to memory cache)
- **AVA**: Frontend visualization library (AntV ecosystem)

## Files to Reference
- Architecture: [domain/README.md](chatbi/domain/README.md)
- Migrations: [migrations/README.md](chatbi/migrations/README.md)  
- DI system: [dependencies.py](chatbi/dependencies.py)
- Connection pooling: [database/drivers/factory.py](chatbi/database/drivers/factory.py)
- Main app: [main.py](chatbi/main.py)
