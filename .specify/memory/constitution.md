<!--
Sync Impact Report: Constitution Update

- Version Change: Created v1.0.0 (Initial Ratification)
- New Principles:
  I. Strict Domain-Driven Design (DDD)
  II. Multi-Database Abstraction
  III. Multi-Agent System
  IV. Repository Pattern & Dependency Injection
  V. Standardized Observability & Response
- Added Sections:
  - Technology Standards
  - Development Workflow
- Follow-up TODOs: None
-->

# ChatBI Constitution

## Core Principles

### I. Strict Domain-Driven Design (DDD)
Business logic MUST reside exclusively in `chatbi/domain/<name>/`. The internal structure of a domain MUST follow the layers: `models.py` (pure domain), `entities.py` (ORM), `dtos.py` (API), `repository.py` (Access), `service.py` (Orchestration), and `router.py` (Endpoints). Cross-domain dependencies MUST be minimal, and imports MUST respect the `__init__.py` export barriers to prevent tight coupling.

### II. Multi-Database Abstraction
Direct database connections are FORBIDDEN in application code. All database access MUST use `chatbi.database.drivers.factory.create_adapter()` via the `ConnectionManager` to ensure pooling constraints (max 50 total). The Application DB (PostgreSQL) and Analytics DB (DuckDB) MUST remain separated; never cross-query without an explicit adapter strategy.

### III. Multi-Agent System
Complex logic MUST be encapsulated in specialized agents inheriting from `AgentBase` (e.g., `SchemaAgent`, `SqlAgent`). Agents MUST communicate via `AgentMessage` only. Prompt engineering artifacts MUST be isolated in `agent/prompts/` and never hardcoded in logic files.

### IV. Repository Pattern & Dependency Injection
Services MUST NOT access SQLAlchemy models or execute queries directly; they MUST use Repositories. All Repositories and Services MUST be injected via `chatbi/dependencies.py`. The dependency injection system MUST be used to handle the distinction between synchronous and asynchronous database sessions automatically.

### V. Standardized Observability & Response
All API responses MUST be wrapped by `StandardResponseMiddleware` to ensure a uniform JSON envelope. All logging MUST use `loguru` and leverage the `RequestLoggerMiddleware` to include the Request ID. Error handling MUST be done by raising domain-specific exceptions, which the global error handler converts to standard HTTP responses.

## Technology Standards

The project MUST adhere to the following stack constraints:
- **Backend**: Python 3.11+ managed by `uv`. FastApi for web server (Async preferred).
- **Frontend**: Node.js 18+ managed by `pnpm`. Umi.js, Ant Design X, AVA charts.
- **Type Safety**: Python functions MUST have type hints; Frontend APIs MUST be generated from OpenAPI via `openapi-fetch`.
- **Linting**: Strict adherence to `ruff` (Python) and `Biome/Prettier` (JS/TS).

## Development Workflow

All development MUST follow these operational procedures:
- **Migrations**: Database schema changes MUST be managed via Alembic (`manage_migrations.py`), never manual SQL.
- **Testing**: New features MUST include `pytest` test cases.
- **Infrastructure**: Local development MUST use `make docker up` to run PostgreSQL, Redis, and Qdrant contexts.
- **Code Style**: Code MUST pass `make lint` and `make format` before commit.

## Governance

This Constitution serves as the primary source of truth for architectural and operational decisions. Any deviation from these principles requires a formal Amendment with a version bump.
- **Compliance**: All Pull Requests MUST be verified against these principles.
- **Versioning**: Semantic Versioning (MAJOR.MINOR.PATCH) applies to this document.
- **Hierarchy**: This document supersedes user stories or verbal agreements if a conflict arises.

**Version**: 1.0.0 | **Ratified**: 2026-01-09 | **Last Amended**: 2026-01-09
