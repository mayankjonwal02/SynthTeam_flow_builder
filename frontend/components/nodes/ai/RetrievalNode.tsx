import { BookOpen } from "lucide-react";
import { createAIExecNode } from "./AIExecNodeFactory";

const a = { border: "border-indigo-400", bg: "bg-indigo-500/10", text: "text-indigo-400", shadow: "shadow-indigo-500/5" };

export default createAIExecNode({
  componentName: "retrieval",
  defaultLabel: "RAG Retrieval",
  accentColor: "indigo",
  accentClasses: a,
  badge: "RAG",
  icon: BookOpen,
  targetHandles: [
    { id: "ai_embedding", label: "Embed", color: "indigo" },
    { id: "ai_vectorstore", label: "VStore", color: "violet" },
  ],
  fields: [
    { key: "top_k", label: "Top K", placeholder: "5" },
  ],
});
