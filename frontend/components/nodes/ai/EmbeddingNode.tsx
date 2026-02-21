import { Layers } from "lucide-react";
import { createAIExecNode } from "./AIExecNodeFactory";

const a = { border: "border-indigo-400", bg: "bg-indigo-500/10", text: "text-indigo-400", shadow: "shadow-indigo-500/5" };

export default createAIExecNode({
  componentName: "embedding_generate",
  defaultLabel: "Generate Embedding",
  accentColor: "indigo",
  accentClasses: a,
  badge: "EMBED",
  icon: Layers,
  targetHandles: [
    { id: "ai_embedding", label: "Embed Model", color: "indigo" },
  ],
  fields: [
    { key: "text_template", label: "Text Template", placeholder: "{{input}}", type: "textarea" },
  ],
});
