import { Globe } from "lucide-react";
import { createConfigNode } from "./ConfigNodeFactory";

const a = { border: "border-amber-400", bg: "bg-amber-500/10", text: "text-amber-400", shadow: "shadow-amber-500/5" };

export default createConfigNode({
  componentName: "tool_web_search",
  defaultLabel: "Web Search",
  accentColor: "amber",
  accentClasses: a,
  handleType: "ai_tool",
  handleLabel: "Tool",
  badge: "TOOL",
  icon: Globe,
  fields: [
    { key: "api_key", label: "Tavily API Key", placeholder: "tvly-...", type: "password" },
    { key: "max_results", label: "Max Results", placeholder: "5", type: "number" },
  ],
});
