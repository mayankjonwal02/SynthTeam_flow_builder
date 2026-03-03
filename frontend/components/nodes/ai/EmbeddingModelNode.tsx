import { Layers } from "lucide-react";
import { createConfigNode } from "./ConfigNodeFactory";

const a = { border: "border-indigo-400", bg: "bg-indigo-500/10", text: "text-indigo-400", shadow: "shadow-indigo-500/5" };

export default createConfigNode({
  componentName: "embedding_model",
  defaultLabel: "Embedding Model",
  accentColor: "indigo",
  accentClasses: a,
  handleType: "ai_embedding",
  handleLabel: "Embed",
  badge: "EMBED",
  icon: Layers,
  fields: [
    { key: "provider", label: "Provider", placeholder: "openai", type: "select", options: ["openai", "ollama", "huggingface"] },
    { key: "model", label: "Model", placeholder: "text-embedding-3-small" },
    { key: "api_key", label: "API Key", placeholder: "sk-...", type: "password" },
  ],
});
