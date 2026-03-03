import { DatabaseZap } from "lucide-react";
import { createConfigNode } from "./ConfigNodeFactory";

const a = { border: "border-amber-400", bg: "bg-amber-500/10", text: "text-amber-400", shadow: "shadow-amber-500/5" };

export default createConfigNode({
  componentName: "tool_db_query",
  defaultLabel: "DB Query",
  accentColor: "amber",
  accentClasses: a,
  handleType: "ai_tool",
  handleLabel: "Tool",
  badge: "TOOL",
  icon: DatabaseZap,
  fields: [
    { key: "db_type", label: "Database Type", placeholder: "postgres", type: "select", options: ["postgres", "mysql", "sqlite", "mongo"] },
    { key: "connection_id", label: "Connection ID / URI", placeholder: "conn-uuid or uri" },
  ],
});
