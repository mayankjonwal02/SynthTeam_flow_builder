import HttpEntryNode from "./HttpEntryNode";
import ProcessorNode from "./ProcessorNode";
import ResponseNode from "./ResponseNode";
import IfConditionNode from "./IfConditionNode";
import SwitchCaseNode from "./SwitchCaseNode";
import LoopForEachNode from "./LoopForEachNode";
import ParallelSplitNode from "./ParallelSplitNode";
import MergeJoinNode from "./MergeJoinNode";
import DelayNode from "./DelayNode";
import WebhookTriggerNode from "./WebhookTriggerNode";
import CronTriggerNode from "./CronTriggerNode";
import ManualTriggerNode from "./ManualTriggerNode";
import HeaderExtractorNode from "./HeaderExtractorNode";
import AuthNodeNode from "./AuthNodeNode";
import PythonFunctionNode from "./PythonFunctionNode";

// PostgreSQL
import PGFindNode from "./db/PGFindNode";
import PGInsertNode from "./db/PGInsertNode";
import PGUpdateNode from "./db/PGUpdateNode";
import PGDeleteNode from "./db/PGDeleteNode";
import PGQueryNode from "./db/PGQueryNode";
import PGTxnStartNode from "./db/PGTxnStartNode";
import PGTxnCommitNode from "./db/PGTxnCommitNode";
import PGTxnRollbackNode from "./db/PGTxnRollbackNode";

// MySQL
import MySQLFindNode from "./db/MySQLFindNode";
import MySQLInsertNode from "./db/MySQLInsertNode";
import MySQLUpdateNode from "./db/MySQLUpdateNode";
import MySQLDeleteNode from "./db/MySQLDeleteNode";
import MySQLQueryNode from "./db/MySQLQueryNode";
import MySQLTxnStartNode from "./db/MySQLTxnStartNode";
import MySQLTxnCommitNode from "./db/MySQLTxnCommitNode";
import MySQLTxnRollbackNode from "./db/MySQLTxnRollbackNode";

// MongoDB
import MongoFindNode from "./db/MongoFindNode";
import MongoInsertNode from "./db/MongoInsertNode";
import MongoUpdateNode from "./db/MongoUpdateNode";
import MongoDeleteNode from "./db/MongoDeleteNode";
import MongoAggregateNode from "./db/MongoAggregateNode";

// SQLite
import SQLiteFindNode from "./db/SQLiteFindNode";
import SQLiteInsertNode from "./db/SQLiteInsertNode";
import SQLiteUpdateNode from "./db/SQLiteUpdateNode";
import SQLiteDeleteNode from "./db/SQLiteDeleteNode";
import SQLiteQueryNode from "./db/SQLiteQueryNode";

// Supabase
import SupaFindNode from "./db/SupaFindNode";
import SupaInsertNode from "./db/SupaInsertNode";
import SupaUpdateNode from "./db/SupaUpdateNode";
import SupaDeleteNode from "./db/SupaDeleteNode";
import SupaQueryNode from "./db/SupaQueryNode";

export const nodeTypes = {
  http_entry: HttpEntryNode,
  processor: ProcessorNode,
  response_builder: ResponseNode,
  if_condition: IfConditionNode,
  switch_case: SwitchCaseNode,
  loop_foreach: LoopForEachNode,
  parallel_split: ParallelSplitNode,
  merge_join: MergeJoinNode,
  delay: DelayNode,
  webhook_trigger: WebhookTriggerNode,
  cron_trigger: CronTriggerNode,
  manual_trigger: ManualTriggerNode,
  header_extractor: HeaderExtractorNode,
  auth_node: AuthNodeNode,
  python_function: PythonFunctionNode,
  pg_find: PGFindNode,
  pg_insert: PGInsertNode,
  pg_update: PGUpdateNode,
  pg_delete: PGDeleteNode,
  pg_raw_query: PGQueryNode,
  pg_txn_start: PGTxnStartNode,
  pg_txn_commit: PGTxnCommitNode,
  pg_txn_rollback: PGTxnRollbackNode,
  mysql_find: MySQLFindNode,
  mysql_insert: MySQLInsertNode,
  mysql_update: MySQLUpdateNode,
  mysql_delete: MySQLDeleteNode,
  mysql_raw_query: MySQLQueryNode,
  mysql_txn_start: MySQLTxnStartNode,
  mysql_txn_commit: MySQLTxnCommitNode,
  mysql_txn_rollback: MySQLTxnRollbackNode,
  mongo_find: MongoFindNode,
  mongo_insert: MongoInsertNode,
  mongo_update: MongoUpdateNode,
  mongo_delete: MongoDeleteNode,
  mongo_aggregate: MongoAggregateNode,
  sqlite_find: SQLiteFindNode,
  sqlite_insert: SQLiteInsertNode,
  sqlite_update: SQLiteUpdateNode,
  sqlite_delete: SQLiteDeleteNode,
  sqlite_raw_query: SQLiteQueryNode,
  supa_find: SupaFindNode,
  supa_insert: SupaInsertNode,
  supa_update: SupaUpdateNode,
  supa_delete: SupaDeleteNode,
  supa_raw_query: SupaQueryNode,
};
