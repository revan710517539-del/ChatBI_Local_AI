# Domain-Driven Design Architecture

This directory contains the core domain models, entities, and business logic for the ChatBI application, organized according to Domain-Driven Design (DDD) principles.

## Directory Structure

```
domain/
  ├── common/             # Shared domain components
  │   ├── entities.py     # Base entity classes for database persistence
  │   └── schemas.py      # Common schema models for API communication
  ├── chat/               # Chat domain
  │   ├── dtos.py         # Data Transfer Objects for chat API
  │   ├── entities.py     # Database entities for chat persistence
  │   └── models.py       # Core domain models for chat functionality
  ├── cube/               # Cube domain
  │   ├── dtos.py         # Data Transfer Objects for cube API
  │   ├── entities.py     # Database entities for cube persistence
  │   └── models.py       # Core domain models for cube functionality
  └── datasource/         # Datasource domain
      ├── dtos.py         # Data Transfer Objects for datasource API
      ├── entities.py     # Database entities for datasource persistence
      └── models.py       # Core domain models for datasource functionality
```

## Domain Model Organization

Each domain follows a consistent structure with clear separation of concerns:

1. **Core Domain Models** (`models.py`):
   - Pure business logic and domain objects
   - Not tied to any persistence or API concerns
   - Represent the core concepts of the domain

2. **Database Entities** (`entities.py`):
   - SQLAlchemy ORM models for database persistence
   - Contains mapping to and from domain models
   - Handles database-specific concerns

3. **Data Transfer Objects** (`dtos.py`):
   - Pydantic models for API request/response validation
   - Handles serialization/deserialization
   - Documents API contracts

## Design Principles

This architecture follows these key principles:

1. **Separation of Concerns**: Each domain encapsulates its own logic, entities, and DTOs.
2. **Domain-First Design**: Business logic is independent of infrastructure concerns.
3. **Rich Domain Models**: Domain models contain behavior, not just data.
4. **Clean Boundary**: Clear separation between domain logic and external interfaces.

## Usage Guidelines

### Creating New Domain Entities

When creating new domain entities, follow these steps:

1. Define core domain models in the appropriate `models.py` file
2. Create SQLAlchemy ORM entities in the related `entities.py` file
3. Implement conversion methods between domain models and entities
4. Define DTOs in the `dtos.py` file for API communication

### Database Access

Database entities should be accessed through repositories, not directly in services:

```python
# Good: Using repository pattern
user = user_repository.get_by_id(user_id)

# Avoid: Direct database access in services
user = session.query(User).filter(User.id == user_id).first()
```

### Importing Guidelines

- Import from the domain package directly for common use cases
- Import from specific domain modules for specialized access

```python
# Common pattern - importing from main domain package
from chatbi.domain import ChatSession, Message, DataSource

# Specialized access - importing from specific domain module
from chatbi.domain.chat.entities import ChatMessage
```