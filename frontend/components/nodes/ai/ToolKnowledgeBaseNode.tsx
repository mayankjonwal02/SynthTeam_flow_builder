import { BookOpen } from "lucide-react";
import { createConfigNode } from "./ConfigNodeFactory";

const a = { border: "border-amber-400", bg: "bg-amber-500/10", text: "text-amber-400", shadow: "shadow-amber-500/5" };

export default createConfigNode({
  componentName: "tool_knowledge_base",
  defaultLabel: "Knowledge Base",
  accentColor: "amber",
  accentClasses: a,
  handleType: "ai_tool",
  handleLabel: "Tool",
  badge: "TOOL",
  icon: BookOpen,
  fields: [
    { key: "data_description", label: "Data Description", placeholder: "Company HR policies, product docs...", type: "textarea" },
    { key: "collection", label: "Collection", placeholder: "default" },
    { key: "top_k", label: "Top K", placeholder: "5", type: "number" },
    { key: "embedding_provider", label: "Embedding Provider", placeholder: "openai", type: "select", options: ["openai", "ollama", "huggingface"] },
    { key: "embedding_model", label: "Embedding Model", placeholder: "text-embedding-3-small" },
    { key: "embedding_api_key", label: "Embedding API Key", placeholder: "sk-...", type: "password" },
    { key: "vectorstore_provider", label: "Vector Store", placeholder: "qdrant", type: "select", options: ["qdrant", "pinecone", "chroma", "weaviate"] },
    { key: "vectorstore_url", label: "Vector Store URL", placeholder: "http://localhost:6333" },
    { key: "vectorstore_api_key", label: "Vector Store API Key", placeholder: "...", type: "password" },
  ],
});
