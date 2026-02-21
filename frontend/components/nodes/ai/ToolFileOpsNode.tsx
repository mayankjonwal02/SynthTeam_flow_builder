import { FileText } from "lucide-react";
import { createConfigNode } from "./ConfigNodeFactory";

const a = { border: "border-amber-400", bg: "bg-amber-500/10", text: "text-amber-400", shadow: "shadow-amber-500/5" };

export default createConfigNode({
  componentName: "tool_file_ops",
  defaultLabel: "File Ops",
  accentColor: "amber",
  accentClasses: a,
  handleType: "ai_tool",
  handleLabel: "Tool",
  badge: "TOOL",
  icon: FileText,
  fields: [
    { key: "mode", label: "Mode", placeholder: "read", type: "select", options: ["read", "write"] },
    { key: "base_path", label: "Base Path", placeholder: "/tmp" },
  ],
});
