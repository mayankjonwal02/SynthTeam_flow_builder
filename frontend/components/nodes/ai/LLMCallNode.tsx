import { Sparkles } from "lucide-react";
import { createAIExecNode } from "./AIExecNodeFactory";

const a = { border: "border-purple-400", bg: "bg-purple-500/10", text: "text-purple-400", shadow: "shadow-purple-500/5" };

export default createAIExecNode({
  componentName: "llm_call",
  defaultLabel: "LLM Call",
  accentColor: "purple",
  accentClasses: a,
  badge: "LLM",
  icon: Sparkles,
  targetHandles: [
    { id: "ai_model", label: "Model", color: "purple" },
    { id: "ai_structure", label: "Schema", color: "emerald" },
  ],
  fields: [
    { key: "system_prompt", label: "System Prompt", placeholder: "You are a helpful assistant...", type: "textarea", sourceKey: "system_prompt_source", placeholderMode: { static: "You are...", input: "input", expression: "input.system_prompt" } },
    { key: "prompt_template", label: "Prompt Template", placeholder: "{{input}}", type: "textarea", sourceKey: "prompt_template_source", placeholderMode: { static: "{{input}}", input: "input", expression: "input.data.query" } },
  ],
});
