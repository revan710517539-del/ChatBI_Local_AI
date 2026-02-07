# ChatBI Copilot Instructions

## Project Overview
ChatBI: Natural language to SQL/visualization BI system. Python/FastAPI backend + TypeScript/React frontend. Uses multi-agent LLM system to convert chat to SQL queries, then visualizes results with AVA charts.

## Architecture

### Multi-Database Pattern
- **Application DB**: PostgreSQL (sessions, configs, metadata)
- **Analytics DB**: DuckDB (embedded, for data analysis)
- **NEVER** create direct DB connections - all connections via `connection_manager.py` with pooling (max 50 total, 10/database)
- Use factory pattern: `create_adapter()` from `chatbi.database.drivers.factory`

### Domain-Driven Design (Strict)
All business logic in `chatbi/domain/<name>/`:
```python
models.py       # Pure domain logic (no DB/API coupling)
entities.py     # SQLAlchemy ORM + to_domain()/from_domain() converters
dtos.py         # Pydantic API schemas
repository.py   # Data access (sync/async methods)
service.py      # Business orchestration
router.py       # FastAPI endpoints
```

Import pattern: `from chatbi.domain import ChatSession, Message` (re-exported via `__init__.py`)

### Multi-Agent System (`chatbi/agent/`)
- **SchemaAgent**: Database schema analysis
- **SqlAgent**: Natural language → SQL using LLM prompts
- **VisualizeAgent**: Query results → chart specs
- All inherit `AgentBase`, return `AgentMessage`, use prompts from `agent/prompts/`

### Dependency Injection
Centralized in `chatbi/dependencies.py`:
```python
# Define once, auto-detects sync/async context
ChatRepoDep = RepositoryDependency(ChatRepository)

@router.get("/sessions")
async def get_sessions(repo: ChatRepository = Depends(ChatRepoDep)):
    return await repo.get_all()
```

Standard deps: `PostgresSessionDep` (sync), `AsyncSessionDep` (async)

## Critical Workflows

### Setup & Running
```bash
make install          # uv sync (Python) + pnpm install (Node)
make docker up        # Start Postgres, Redis, Cube.js
make dev-server       # FastAPI on :8000
make dev-client       # React dev on :8001
make gen-api          # Regenerate client types from OpenAPI
```

### Database Migrations (Alembic)
```bash
# After changing entities.py
uv run python -m chatbi.migrations.manage_migrations create "description"
uv run python -m chatbi.migrations.manage_migrations upgrade
```

### Testing & Formatting
```bash
make test             # pytest
make format           # ruff + taplo (auto-fix)
make lint             # ruff check-only
```

## Code Patterns

### Transaction Management
Use `@transactional` decorator (from `chatbi.dependencies`):
```python
@transactional
async def update_session(self, session_id: UUID, data: dict):
    # Auto-commits on success, rolls back on error
```

### Repository Pattern (REQUIRED)
❌ Never query SQLAlchemy directly in services:
```python
# Bad
sessions = session.query(ChatSession).filter_by(user_id=id).all()
```

✅ Always use repositories:
```python
# Good
sessions = await chat_repository.get_by_user_id(id)
```

### Caching
- Abstract interface: `chatbi/cache/base.py`
- Implementations: `MemoryCache` (dev), `RedisCache` (prod)
- Validator: `@requires_cache(required_fields=["sql", "schema"])`

### Response Standardization
All API responses wrapped by `StandardResponseMiddleware` in uniform format. Use FastAPI error handlers registered in `middleware/error_handler.py`.

## Environment Variables (.env)
Required from `.env.example`:
```bash
LLM_API_KEY, LLM_BASE_URL, LLM_MODEL    # OpenAI/Tongyi/DeepSeek compatible
DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS  # PostgreSQL
CUBE_SERVICE_API=http://localhost:4000  # Optional OLAP layer
```

## Tech Stack Specifics

### Python
- **Version**: 3.11+ (uses `uv`, NOT pip)
- **Async**: Prefer async endpoints unless DB ops are purely sync
- **Logging**: Loguru with auto request ID tracking (`logger.info()`)
- **Type hints**: Required on all functions

### Frontend (web
- **Framework**: Umi.js + Ant Design X (chat UI) + AVA (charts)
- **API**: Type-safe via `openapi-fetch` from auto-generated `api-schema.ts`
- **Node**: 18+ (uses native fetch)

### Middleware Stack (in order)
1. `RequestLoggerMiddleware`: Request ID + logging
2. `StandardResponseMiddleware`: Uniform response format
3. CORS: localhost:8001 allowed
4. Error handlers: Domain exceptions → HTTP responses

## Adding New Components

### New Domain
1. Create `domain/<name>/` with full DDD structure
2. Export in `domain/<name>/__init__.py` and `domain/__init__.py`
3. Register router in `routers/__init__.py`
4. Create migration

### New Database Adapter
1. Create `database/drivers/<db>_adapter.py` extending `DatabaseAdapter`
2. Add `DatabaseType` enum in `domain/datasource/models.py`
3. Register in `factory.py`'s `_adapter_registry`
4. Implement: `connect()`, `disconnect()`, `execute_query()`, `get_schema()`

### New Agent
1. Create `agent/<name>_agent.py` inheriting `AgentBase`
2. Implement `replay(**kwargs) -> AgentMessage`
3. Add prompts in `agent/prompts/`
4. Integrate in service layer

## Key Files
- [chatbi/domain/README.md](chatbi/domain/README.md): DDD architecture
- [chatbi/migrations/README.md](chatbi/migrations/README.md): Migration guide
- [chatbi/dependencies.py](chatbi/dependencies.py): DI system
- [chatbi/database/drivers/factory.py](chatbi/database/drivers/factory.py): Connection pooling
