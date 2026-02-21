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

// AI Config Nodes
import LLMModelNode from "./ai/LLMModelNode";
import OutputStructureNode from "./ai/OutputStructureNode";
import MemoryConfigNode from "./ai/MemoryConfigNode";
import EmbeddingModelNode from "./ai/EmbeddingModelNode";
import VectorStoreConfigNode from "./ai/VectorStoreConfigNode";

// AI Tool Nodes
import ToolWebSearchNode from "./ai/ToolWebSearchNode";
import ToolHttpNode from "./ai/ToolHttpNode";
import ToolCalculatorNode from "./ai/ToolCalculatorNode";
import ToolDBQueryNode from "./ai/ToolDBQueryNode";
import ToolCodeNode from "./ai/ToolCodeNode";
import ToolFileOpsNode from "./ai/ToolFileOpsNode";
import ToolEmailNode from "./ai/ToolEmailNode";
import ToolGmailNode from "./ai/ToolGmailNode";
import ToolSlackNode from "./ai/ToolSlackNode";
import ToolWorkflowNode from "./ai/ToolWorkflowNode";
import ToolComposioNode from "./ai/ToolComposioNode";
import ToolKnowledgeBaseNode from "./ai/ToolKnowledgeBaseNode";

// RAG Pipeline Nodes
import DocLoaderNode from "./ai/DocLoaderNode";
import TextSplitterNode from "./ai/TextSplitterNode";

// AI Execution Nodes
import LLMCallNode from "./ai/LLMCallNode";
import EmbeddingNode from "./ai/EmbeddingNode";
import VectorUpsertNode from "./ai/VectorUpsertNode";
import VectorSearchNode from "./ai/VectorSearchNode";
import VectorDeleteNode from "./ai/VectorDeleteNode";
import RetrievalNode from "./ai/RetrievalNode";
import AgentRunNode from "./ai/AgentRunNode";
import AutonomousAgentNode from "./ai/AutonomousAgentNode";
import VisionNode from "./ai/VisionNode";
import STTNode from "./ai/STTNode";
import TTSNode from "./ai/TTSNode";

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
  // AI Config
  llm_model: LLMModelNode,
  output_structure: OutputStructureNode,
  memory_config: MemoryConfigNode,
  embedding_model: EmbeddingModelNode,
  vectorstore_config: VectorStoreConfigNode,
  // AI Tools
  tool_web_search: ToolWebSearchNode,
  tool_http_request: ToolHttpNode,
  tool_calculator: ToolCalculatorNode,
  tool_db_query: ToolDBQueryNode,
  tool_code_executor: ToolCodeNode,
  tool_file_ops: ToolFileOpsNode,
  tool_email: ToolEmailNode,
  tool_gmail: ToolGmailNode,
  tool_slack: ToolSlackNode,
  tool_workflow: ToolWorkflowNode,
  tool_composio: ToolComposioNode,
  tool_knowledge_base: ToolKnowledgeBaseNode,
  // RAG Pipeline
  doc_loader: DocLoaderNode,
  text_splitter: TextSplitterNode,
  // AI Execution
  llm_call: LLMCallNode,
  embedding_generate: EmbeddingNode,
  vector_upsert: VectorUpsertNode,
  vector_search: VectorSearchNode,
  vector_delete: VectorDeleteNode,
  retrieval: RetrievalNode,
  agent_run: AgentRunNode,
  autonomous_agent: AutonomousAgentNode,
  vision_analyze: VisionNode,
  speech_to_text: STTNode,
  text_to_speech: TTSNode,
};
