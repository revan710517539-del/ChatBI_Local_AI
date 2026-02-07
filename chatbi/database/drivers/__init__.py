"""
Database drivers package.

This package contains adapters for different database engines,
providing a unified interface for connecting to and querying different types of databases.
"""

from chatbi.database.drivers.base import ConnectionInfo, DatabaseAdapter
from chatbi.database.drivers.factory import get_adapter

__all__ = ["DatabaseAdapter", "ConnectionInfo", "get_adapter"]
