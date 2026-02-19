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
};
