import { Brain } from "lucide-react";
import { createConfigNode } from "./ConfigNodeFactory";

const a = { border: "border-cyan-400", bg: "bg-cyan-500/10", text: "text-cyan-400", shadow: "shadow-cyan-500/5" };

export default createConfigNode({
  componentName: "memory_config",
  defaultLabel: "Memory",
  accentColor: "cyan",
  accentClasses: a,
  handleType: "ai_memory",
  handleLabel: "Memory",
  badge: "MEM",
  icon: Brain,
  fields: [
    { key: "backend", label: "Backend", placeholder: "in_memory", type: "select", options: ["in_memory", "redis", "vector"] },
    { key: "session_id", label: "Session ID", placeholder: "default" },
    { key: "max_messages", label: "Max Messages", placeholder: "50", type: "number" },
    { key: "redis_url", label: "Redis URL (if redis)", placeholder: "redis://localhost:6379" },
  ],
});
