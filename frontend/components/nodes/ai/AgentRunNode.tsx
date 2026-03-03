import { Bot } from "lucide-react";
import { createAIExecNode } from "./AIExecNodeFactory";

const a = { border: "border-pink-400", bg: "bg-pink-500/10", text: "text-pink-400", shadow: "shadow-pink-500/5" };

export default createAIExecNode({
  componentName: "agent_run",
  defaultLabel: "Agent (ReAct)",
  accentColor: "pink",
  accentClasses: a,
  badge: "AGENT",
  icon: Bot,
  targetHandles: [
    { id: "ai_model", label: "Model", color: "purple" },
    { id: "ai_tool", label: "Tools", color: "amber" },
    { id: "ai_memory", label: "Memory", color: "cyan" },
    { id: "ai_structure", label: "Schema", color: "emerald" },
    { id: "ai_embedding", label: "Embed", color: "indigo" },
    { id: "ai_vectorstore", label: "VStore", color: "violet" },
    { id: "ai_subagent", label: "Sub-Agents", color: "pink" },
  ],
  fields: [
    { key: "system_prompt", label: "System Prompt", placeholder: "You are a helpful assistant...", type: "textarea", sourceKey: "system_prompt_source", placeholderMode: { static: "You are...", input: "input", expression: "input.system_prompt" } },
    { key: "prompt_template", label: "Prompt / Goal", placeholder: "{{input}}", type: "textarea", sourceKey: "prompt_template_source", placeholderMode: { static: "{{input}}", input: "input", expression: "input.data.query" } },
    { key: "max_iterations", label: "Max Iterations", placeholder: "10" },
  ],
});
