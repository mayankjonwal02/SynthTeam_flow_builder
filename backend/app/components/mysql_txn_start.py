"""MySQL Transaction Start."""
from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.db_base_mixin import DBNodeMixin

@register_component("mysql_txn_start")
class MySQLTxnStartComponent(DBNodeMixin, BaseComponent):
    DB_TYPE = "mysql"
    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        merged = self._merge_inputs(inputs)
        connector = await self._get_connector(config)
        txn = await connector.begin_transaction()
        merged["__db_txn__"] = txn
        merged["__db_conn_id__"] = config.get("connection_id", "")
        return merged
