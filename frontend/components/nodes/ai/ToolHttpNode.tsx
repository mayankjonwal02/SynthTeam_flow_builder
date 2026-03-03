import { Send } from "lucide-react";
import { createConfigNode } from "./ConfigNodeFactory";

const a = { border: "border-amber-400", bg: "bg-amber-500/10", text: "text-amber-400", shadow: "shadow-amber-500/5" };

export default createConfigNode({
  componentName: "tool_http_request",
  defaultLabel: "HTTP Request",
  accentColor: "amber",
  accentClasses: a,
  handleType: "ai_tool",
  handleLabel: "Tool",
  badge: "TOOL",
  icon: Send,
  fields: [
    { key: "allowed_methods", label: "Allowed Methods", placeholder: "GET,POST" },
    { key: "timeout", label: "Timeout (sec)", placeholder: "30", type: "number" },
  ],
});
