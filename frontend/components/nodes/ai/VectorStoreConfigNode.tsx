import { Database } from "lucide-react";
import { createConfigNode } from "./ConfigNodeFactory";

const a = { border: "border-violet-400", bg: "bg-violet-500/10", text: "text-violet-400", shadow: "shadow-violet-500/5" };

export default createConfigNode({
  componentName: "vectorstore_config",
  defaultLabel: "Vector Store",
  accentColor: "violet",
  accentClasses: a,
  handleType: "ai_vectorstore",
  handleLabel: "VStore",
  badge: "VECTOR",
  icon: Database,
  fields: [
    { key: "provider", label: "Provider", placeholder: "qdrant", type: "select", options: ["qdrant", "pinecone", "weaviate", "chroma", "supabase"] },
    { key: "collection", label: "Collection", placeholder: "default" },
    { key: "url", label: "URL", placeholder: "http://localhost:6333" },
    { key: "api_key", label: "API Key", placeholder: "...", type: "password" },
  ],
});
