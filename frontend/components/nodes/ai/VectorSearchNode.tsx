import { Search } from "lucide-react";
import { createAIExecNode } from "./AIExecNodeFactory";

const a = { border: "border-indigo-400", bg: "bg-indigo-500/10", text: "text-indigo-400", shadow: "shadow-indigo-500/5" };

export default createAIExecNode({
  componentName: "vector_search",
  defaultLabel: "Vector Search",
  accentColor: "indigo",
  accentClasses: a,
  badge: "SEARCH",
  icon: Search,
  targetHandles: [
    { id: "ai_vectorstore", label: "VStore", color: "violet" },
  ],
  fields: [
    { key: "top_k", label: "Top K", placeholder: "5" },
  ],
});
