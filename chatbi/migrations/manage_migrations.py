#!/usr/bin/env python
"""
Migration management script.

This script provides common migration operations similar to Flyway in Java,
but using Alembic as the underlying engine for Python.

Usage:
    python -m chatbi.models.migrations.manage_migrations [command]

Commands:
    status        Show current migration status
    init          Initialize migrations (run first migration)
    create [msg]  Create a new migration with optional message
    upgrade       Upgrade to the latest version
    downgrade     Downgrade by one version
    history       Show migration history
    reset         Reset the database (DROP + recreate)

Example:
    python -m chatbi.models.migrations.manage_migrations create "Add user table"
"""

import argparse
import os
import subprocess
import sys
from typing import List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

from chatbi.config import get_config

config = get_config()

# Create a connection URL without the database name
engine_url = f"postgresql://{config.database.user}:{config.database.password}@{config.database.host}:{config.database.port}/postgres"

# Ensure we can import from the project root
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
)


def run_alembic_command(args: list[str], verbose: bool = True) -> int:
    """Run an Alembic command with proper environment setup."""
    # Convert to string for subprocess
    cmd = ["alembic"] + args

    if verbose:
        print(f"Executing: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=not verbose, check=False)
        if result.returncode != 0 and not verbose:
            print("Error executing alembic command:")
            print(result.stderr.decode())
        return result.returncode
    except Exception as e:
        print(f"Error executing command: {e}")
        return 1


def check_db_exists() -> bool:
    """Check if the database exists."""
    engine = create_engine(engine_url)

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    f"SELECT 1 FROM pg_database WHERE datname = '{config.database.name}'"
                )
            )
            return result.scalar() is not None
    except Exception as e:
        print(f"Error checking if database exists: {e}")
        return False


def create_database() -> bool:
    """Create the database if it doesn't exist."""
    engine = create_engine(engine_url)

    try:
        with engine.connect() as conn:
            # We need to commit any existing transaction before executing commands
            conn.execute(text("COMMIT"))

            # Disconnect all other users
            conn.execute(
                text(
                    f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{config.database.name}' AND pid <> pg_backend_pid()"
                )
            )
            # Create the database
            conn.execute(text(f"CREATE DATABASE {config.database.name}"))
            return True
    except Exception as e:
        print(f"Error creating database: {e}")
        return False


def drop_database() -> bool:
    """Drop the database if it exists."""
    engine = create_engine(engine_url)

    try:
        with engine.connect() as conn:
            # We need to commit any existing transaction before executing commands
            conn.execute(text("COMMIT"))

            conn.execute(
                text(
                    f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{config.database.name}' AND pid <> pg_backend_pid()"
                )
            )
            conn.execute(text(f"DROP DATABASE IF EXISTS {config.database.name}"))
        return True
    except Exception as e:
        print(f"Error dropping database: {e}")
        return False


def reset_database() -> bool:
    """Reset the database by dropping and recreating it."""
    if drop_database():
        return create_database()
    return False


def cmd_status() -> int:
    """Show current migration status."""
    return run_alembic_command(["current"])


def cmd_init() -> int:
    """Initialize migrations."""
    if not check_db_exists():
        print("Database does not exist. Creating...")
        if not create_database():
            return 1

    return run_alembic_command(["upgrade", "head"])


def cmd_create(message: Optional[str] = None) -> int:
    """Create a new migration."""
    args = ["revision", "--autogenerate"]

    if message:
        args.extend(["-m", message])
    else:
        args.extend(["-m", "Migration"])

    return run_alembic_command(args)


def cmd_upgrade(version: str = "head") -> int:
    """Upgrade to a specific version or head."""
    return run_alembic_command(["upgrade", version])


def cmd_downgrade(steps: str = "-1") -> int:
    """Downgrade by a specific number of steps."""
    return run_alembic_command(["downgrade", steps])


def cmd_history() -> int:
    """Show migration history."""
    return run_alembic_command(["history"])


def cmd_reset() -> int:
    """Reset the database."""
    if reset_database():
        print("Database reset complete. Now running migrations...")
        return cmd_init()
    return 1


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Manage database migrations")
    parser.add_argument(
        "command",
        choices=[
            "status",
            "init",
            "create",
            "upgrade",
            "downgrade",
            "history",
            "reset",
        ],
        help="Command to execute",
    )
    parser.add_argument("args", nargs="*", help="Additional arguments for the command")

    args = parser.parse_args()

    if args.command == "status":
        return cmd_status()
    elif args.command == "init":
        return cmd_init()
    elif args.command == "create":
        message = args.args[0] if args.args else None
        return cmd_create(message)
    elif args.command == "upgrade":
        version = args.args[0] if args.args else "head"
        return cmd_upgrade(version)
    elif args.command == "downgrade":
        steps = args.args[0] if args.args else "-1"
        return cmd_downgrade(steps)
    elif args.command == "history":
        return cmd_history()
    elif args.command == "reset":
        return cmd_reset()

    print(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
