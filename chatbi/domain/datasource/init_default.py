"""
Initialize default datasource on startup.

This module provides utilities to automatically create a default datasource
when the application starts, using configuration from docker-compose.
"""

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from chatbi.config import get_config
from chatbi.database.database import get_async_session_direct
from chatbi.database.connection_manager import ConnectionManager
from chatbi.domain.datasource import (
    DatabaseType,
    DataSourceCreate,
    DataSourceStatus,
)
from chatbi.domain.datasource.entities import Datasource
from chatbi.domain.datasource.repository import DatasourceRepository


async def init_default_datasource():
    """
    Initialize the default PostgreSQL datasource from Docker configuration.
    
    Creates a datasource pointing to the Docker PostgreSQL instance if it doesn't exist.
    Uses environment variables or defaults to Docker Compose values.
    """
    session: AsyncSession | None = None
    try:
        config = get_config()
        
        # Get async session
        session = await get_async_session_direct()
        
        # Create repository
        repo = DatasourceRepository(session)
        
        # Check if default datasource already exists
        existing = await repo.get_by_name('Default PostgreSQL')
        if existing:
            logger.info("Default datasource 'Default PostgreSQL' already exists, skipping initialization")
            return
        
        # Get connection details from environment or use Docker defaults
        db_host = getattr(config, 'db_host', 'localhost')
        db_port = getattr(config, 'db_port', 15432)
        db_name = getattr(config, 'db_name', 'chatbi_demo')  # Changed to chatbi_demo
        db_user = getattr(config, 'db_user', 'chatbi')
        db_password = getattr(config, 'db_password', '12345')
        
        # Create connection info
        connection_info = {
            'host': db_host,
            'port': db_port,
            'database': db_name,
            'user': db_user,
            'password': db_password,
        }
        
        # Test connection before creating
        success, message, details = await ConnectionManager.test_connection(
            DatabaseType.POSTGRES, connection_info
        )
        
        if not success:
            logger.warning(f"Default datasource connection test failed: {message}")
            logger.warning("Skipping default datasource creation")
            return
        
        # Create datasource
        datasource_data = {
            'name': 'Default PostgreSQL',
            'description': 'Default PostgreSQL datasource from Docker',
            'type': DatabaseType.POSTGRES.value,
            'status': DataSourceStatus.ACTIVE.value,
            'connection_info': connection_info,
            'is_default': True,
        }
        
        # Save to database
        datasource = Datasource(**datasource_data)
        await repo.create(datasource)
        
        # Commit the transaction
        await session.commit()
        
        logger.info(f"✅ Default datasource created successfully: {datasource.name}")
        
    except Exception as e:
        logger.error(f"Failed to initialize default datasource: {e}")
        # Rollback on error
        if session:
            await session.rollback()
        # Don't raise - let the app continue even if default datasource fails
    finally:
        if session:
            await session.close()
