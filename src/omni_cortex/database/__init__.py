"""Database layer for Omni Cortex - SQLite with FTS5."""

from .connection import get_connection, init_database, close_connection
from .schema import SCHEMA_VERSION, get_schema_sql

__all__ = [
    "get_connection",
    "init_database",
    "close_connection",
    "SCHEMA_VERSION",
    "get_schema_sql",
]
