import { FileUp } from "lucide-react";
import { createConfigNode } from "./ConfigNodeFactory";

const a = { border: "border-teal-400", bg: "bg-teal-500/10", text: "text-teal-400", shadow: "shadow-teal-500/5" };

export default createConfigNode({
  componentName: "doc_loader",
  defaultLabel: "Document Loader",
  accentColor: "teal",
  accentClasses: a,
  handleType: "default",
  handleLabel: "",
  badge: "LOAD",
  icon: FileUp,
  fields: [
    { key: "source_type", label: "Source Type", placeholder: "text", type: "select", options: ["text", "url", "file"] },
    { key: "text", label: "Text / Content", placeholder: "Paste document text here...", type: "textarea" },
    { key: "url", label: "URL (if url)", placeholder: "https://example.com/doc.txt" },
    { key: "file_path", label: "File Path (if file)", placeholder: "/data/document.txt" },
  ],
});
