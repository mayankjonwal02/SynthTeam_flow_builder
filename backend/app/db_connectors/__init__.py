"""
Database connector subsystem.

Import this package to auto-register all connectors.
"""

import app.db_connectors.postgres_connector   # noqa: F401
import app.db_connectors.mysql_connector      # noqa: F401
import app.db_connectors.mongo_connector      # noqa: F401
import app.db_connectors.sqlite_connector     # noqa: F401
import app.db_connectors.supabase_connector   # noqa: F401
