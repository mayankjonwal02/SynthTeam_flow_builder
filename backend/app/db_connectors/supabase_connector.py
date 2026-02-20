"""
Supabase connector -- wraps PostgresConnector since Supabase
uses standard PostgreSQL under the hood.

Credentials format:
{
    "host": "db.xxxx.supabase.co",
    "port": 5432,
    "username": "postgres",
    "password": "your-password",
    "database": "postgres"
}
"""

from app.db_connectors.connector_registry import register_connector
from app.db_connectors.postgres_connector import PostgresConnector


@register_connector("supabase")
class SupabaseConnector(PostgresConnector):
    """Supabase uses standard Postgres -- inherit everything."""
    pass
