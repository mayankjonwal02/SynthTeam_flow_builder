"""MySQL Transaction Commit."""
from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.db_base_mixin import DBNodeMixin, ACTIVE_POOLS

@register_component("mysql_txn_commit")
class MySQLTxnCommitComponent(DBNodeMixin, BaseComponent):
    DB_TYPE = "mysql"
    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        merged = self._merge_inputs(inputs)
        txn = merged.get("__db_txn__")
        conn_id = merged.get("__db_conn_id__", "")
        connector = ACTIVE_POOLS.get(conn_id)
        if connector:
            await connector.commit(txn)
        return {k: v for k, v in merged.items() if not k.startswith("__db_")}
