"""
Cron Trigger Component — entry-point node for scheduled workflows.

Config:
    {
        "cron_expression": "*/5 * * * *",
        "is_entry": true
    }

When the workflow is deployed, the registry detects the cron_trigger
entry node and registers a background APScheduler job that invokes
the executor on the configured schedule.

The component itself passes an empty dict through (there is no HTTP
request body when triggered by cron).
"""

from typing import Any, Dict

from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("cron_trigger")
class CronTriggerComponent(BaseComponent):
    """Entry point for cron-scheduled workflows. Passes empty data through."""

    async def execute(
        self,
        request_data: dict,
        inputs: Dict[str, Any],
        config: dict,
    ) -> dict:
        return dict(request_data) if request_data else {}
