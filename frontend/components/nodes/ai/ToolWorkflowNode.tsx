import { Workflow } from "lucide-react";
import { createConfigNode } from "./ConfigNodeFactory";

const a = { border: "border-amber-400", bg: "bg-amber-500/10", text: "text-amber-400", shadow: "shadow-amber-500/5" };

export default createConfigNode({
  componentName: "tool_workflow",
  defaultLabel: "Workflow Invoker",
  accentColor: "amber",
  accentClasses: a,
  handleType: "ai_tool",
  handleLabel: "Tool",
  badge: "TOOL",
  icon: Workflow,
  fields: [
    { key: "workflow_url", label: "Workflow URL", placeholder: "http://localhost:8000/api/..." },
    { key: "method", label: "Method", placeholder: "POST", type: "select", options: ["GET", "POST", "PUT", "DELETE"] },
  ],
});
