"""
Alembic environment configuration.

This file is used to configure how Alembic interacts with your database.
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

# Add the project root directory to the Python path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
)

# Import all models so Alembic can detect them
from chatbi.config import get_config
from chatbi.domain.common.entities import Base
from chatbi.domain.datasource.entities import Datasource
from chatbi.domain.chat.entities import ChatSession, ChatMessage, ChatHistory
from chatbi.domain.auth.entities import UserEntity, UserSessionEntity
from chatbi.domain.mdl.entities import MDLProjectEntity, MDLModelEntity, MDLColumnEntity
from chatbi.domain.diagnosis.entities import DiagnosisResult, CorrectionLog
# Import other models as needed

# Load application config
app_config = get_config()

# Read alembic.ini configuration
config = context.config

# Set SQLAlchemy URL from environment variables
section = config.config_ini_section
config.set_section_option(section, "DB_USER", app_config.database.user)
config.set_section_option(section, "DB_PASSWORD", app_config.database.password)
config.set_section_option(section, "DB_HOST", app_config.database.host)
config.set_section_option(section, "DB_PORT", str(app_config.database.port))
config.set_section_option(section, "DB_NAME", app_config.database.name)

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the SQLAlchemy MetaData object for autogenerating migrations
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
