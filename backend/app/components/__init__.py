"""
Backend node components — each mirrors a frontend ReactFlow node type.

Components self-register via the @register_component decorator when imported.
Import this package once at app startup (main.py) to activate all components.
"""

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
import app.components.python_function    # noqa: F401

from app.components.component_registry import COMPONENT_REGISTRY
from app.components.processor import EchoProcessorComponent

COMPONENT_REGISTRY["processor"] = EchoProcessorComponent
