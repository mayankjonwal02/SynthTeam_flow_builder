import { Wand2 } from "lucide-react";
import { createAIExecNode } from "./AIExecNodeFactory";

const a = { border: "border-pink-400", bg: "bg-pink-500/10", text: "text-pink-400", shadow: "shadow-pink-500/5" };

export default createAIExecNode({
  componentName: "autonomous_agent",
  defaultLabel: "Autonomous Agent",
  accentColor: "pink",
  accentClasses: a,
  badge: "AUTO",
  icon: Wand2,
  targetHandles: [
    { id: "ai_model", label: "Model", color: "purple" },
    { id: "ai_tool", label: "Tools", color: "amber" },
    { id: "ai_memory", label: "Memory", color: "cyan" },
    { id: "ai_embedding", label: "Embed", color: "indigo" },
    { id: "ai_vectorstore", label: "VStore", color: "violet" },
    { id: "ai_subagent", label: "Sub-Agents", color: "pink" },
  ],
  fields: [
    { key: "system_prompt", label: "System Prompt", placeholder: "You are an autonomous agent...", type: "textarea", sourceKey: "system_prompt_source", placeholderMode: { static: "You are...", input: "input", expression: "input.system_prompt" } },
    { key: "goal", label: "Goal", placeholder: "{{input}}", type: "textarea", sourceKey: "goal_source", placeholderMode: { static: "{{input}}", input: "input", expression: "input.data.goal" } },
    { key: "max_iterations", label: "Max Steps", placeholder: "10" },
  ],
});
