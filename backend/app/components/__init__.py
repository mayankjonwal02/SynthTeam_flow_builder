"""
Backend node components — each mirrors a frontend ReactFlow node type.

Components self-register via the @register_component decorator when imported.
Import this package once at app startup (main.py) to activate all components.
"""

# ── Core nodes ───────────────────────────────────────────────────────
import app.components.http_entry          # noqa: F401
import app.components.processor           # noqa: F401
import app.components.response_builder    # noqa: F401
import app.components.if_condition        # noqa: F401
import app.components.switch_case         # noqa: F401
import app.components.loop_foreach        # noqa: F401
import app.components.parallel_split      # noqa: F401
import app.components.merge_join          # noqa: F401
import app.components.delay               # noqa: F401
import app.components.cron_trigger        # noqa: F401
import app.components.webhook_trigger     # noqa: F401
import app.components.manual_trigger      # noqa: F401
import app.components.header_extractor    # noqa: F401
import app.components.auth_node           # noqa: F401
import app.components.python_function     # noqa: F401

# ── PostgreSQL nodes ─────────────────────────────────────────────────
import app.components.pg_find             # noqa: F401
import app.components.pg_insert           # noqa: F401
import app.components.pg_update           # noqa: F401
import app.components.pg_delete           # noqa: F401
import app.components.pg_raw_query        # noqa: F401
import app.components.pg_txn_start        # noqa: F401
import app.components.pg_txn_commit       # noqa: F401
import app.components.pg_txn_rollback     # noqa: F401

# ── MySQL nodes ──────────────────────────────────────────────────────
import app.components.mysql_find          # noqa: F401
import app.components.mysql_insert        # noqa: F401
import app.components.mysql_update        # noqa: F401
import app.components.mysql_delete        # noqa: F401
import app.components.mysql_raw_query     # noqa: F401
import app.components.mysql_txn_start     # noqa: F401
import app.components.mysql_txn_commit    # noqa: F401
import app.components.mysql_txn_rollback  # noqa: F401

# ── MongoDB nodes ────────────────────────────────────────────────────
import app.components.mongo_find          # noqa: F401
import app.components.mongo_insert        # noqa: F401
import app.components.mongo_update        # noqa: F401
import app.components.mongo_delete        # noqa: F401
import app.components.mongo_aggregate     # noqa: F401

# ── SQLite nodes ─────────────────────────────────────────────────────
import app.components.sqlite_find         # noqa: F401
import app.components.sqlite_insert       # noqa: F401
import app.components.sqlite_update       # noqa: F401
import app.components.sqlite_delete       # noqa: F401
import app.components.sqlite_raw_query    # noqa: F401

# ── Supabase nodes ───────────────────────────────────────────────────
import app.components.supa_find           # noqa: F401
import app.components.supa_insert         # noqa: F401
import app.components.supa_update         # noqa: F401
import app.components.supa_delete         # noqa: F401
import app.components.supa_raw_query      # noqa: F401

# ── Aliases ──────────────────────────────────────────────────────────
from app.components.component_registry import COMPONENT_REGISTRY
from app.components.processor import EchoProcessorComponent

COMPONENT_REGISTRY["processor"] = EchoProcessorComponent
