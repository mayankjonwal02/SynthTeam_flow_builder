import { Code2 } from "lucide-react";
import { createConfigNode } from "./ConfigNodeFactory";

const a = { border: "border-amber-400", bg: "bg-amber-500/10", text: "text-amber-400", shadow: "shadow-amber-500/5" };

export default createConfigNode({
  componentName: "tool_code_executor",
  defaultLabel: "Code Executor",
  accentColor: "amber",
  accentClasses: a,
  handleType: "ai_tool",
  handleLabel: "Tool",
  badge: "TOOL",
  icon: Code2,
  fields: [
    { key: "timeout", label: "Timeout (sec)", placeholder: "10", type: "number" },
  ],
});
