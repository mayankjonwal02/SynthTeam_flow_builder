import { Cpu } from "lucide-react";
import { createConfigNode } from "./ConfigNodeFactory";

const a = { border: "border-purple-400", bg: "bg-purple-500/10", text: "text-purple-400", shadow: "shadow-purple-500/5" };

export default createConfigNode({
  componentName: "llm_model",
  defaultLabel: "LLM Model",
  accentColor: "purple",
  accentClasses: a,
  handleType: "ai_model",
  handleLabel: "Model",
  badge: "CONFIG",
  icon: Cpu,
  fields: [
    { key: "provider", label: "Provider", placeholder: "openai", type: "select", options: ["openai", "anthropic", "gemini", "ollama", "groq", "mistral"] },
    { key: "model", label: "Model", placeholder: "gpt-4o-mini" },
    { key: "api_key", label: "API Key", placeholder: "sk-...", type: "password" },
    { key: "temperature", label: "Temperature", placeholder: "0.7", type: "number" },
    { key: "base_url", label: "Base URL (optional)", placeholder: "https://..." },
  ],
});
