# Database Migrations Guide

## Overview

This project uses Alembic for database migrations. All migrations are located in `chatbi/migrations/versions/`.

## Current Migration State

**Single Initial Migration**: `0001_initial_schema.py`

This migration creates all necessary tables for the ChatBI application:

### Core Tables
- `datasources` - Database connection configurations
- `chat_sessions` - Chat conversation sessions
- `chat_messages` - Individual messages in sessions
- `visualizations` - Chart configurations for results
- `query_history` - SQL execution history
- `chat_history` - Conversation analytics

### User Management
- `app_users` - User accounts
- `user_sessions` - User authentication sessions
- `saved_queries` - User-saved SQL queries

### MDL (Metadata Definition Layer)
- `mdl_projects` - MDL project definitions
- `mdl_models` - Data models
- `mdl_fields` - Model fields
- `mdl_relationships` - Model relationships

### Diagnosis System
- `error_patterns` - Error pattern definitions
- `sql_corrections` - SQL correction history

## Migration Commands

### Check Current Migration Status
```bash
uv run python -m chatbi.migrations.manage_migrations status
```

### Create a New Migration
```bash
uv run python -m chatbi.migrations.manage_migrations create "description of change"
```

### Apply Migrations
```bash
uv run python -m chatbi.migrations.manage_migrations upgrade
```

### Rollback Migration
```bash
uv run python -m chatbi.migrations.manage_migrations downgrade
```

### View Migration History
```bash
uv run python -m chatbi.migrations.manage_migrations history
```

## Fresh Database Setup

For a completely fresh database setup:

1. Drop and recreate the database:
   ```bash
   docker exec chatbi-postgres psql -U chatbi -d postgres -c "DROP DATABASE IF EXISTS chatbi;"
   docker exec chatbi-postgres psql -U chatbi -d postgres -c "CREATE DATABASE chatbi;"
   ```

2. Run the initial migration:
   ```bash
   uv run python -m chatbi.migrations.manage_migrations upgrade
   ```

3. The default datasource will be created automatically on application startup.

## Bootstrap Script

Alternatively, use the bootstrap SQL script for quick setup:

```bash
docker exec -i chatbi-postgres psql -U chatbi -d chatbi < init_app_tables.sql
```

Then update the alembic version:

```bash
docker exec chatbi-postgres psql -U chatbi -d chatbi -c "INSERT INTO alembic_version (version_num) VALUES ('0001_initial_schema') ON CONFLICT DO NOTHING;"
```

## Notes

- **Cube tables removed**: Previous `cubes` and `cube_fields` tables have been removed as Cube.js integration is deprecated
- **Single migration approach**: This project uses a single initial migration for simplicity
- **Database separation**: 
  - `chatbi` database: Application metadata (users, sessions, etc.)
  - `chatbi_demo` database: Business data (products, orders, etc.)
