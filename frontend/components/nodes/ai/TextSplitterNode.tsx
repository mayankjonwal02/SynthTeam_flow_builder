import { Scissors } from "lucide-react";
import { createConfigNode } from "./ConfigNodeFactory";

const a = { border: "border-teal-400", bg: "bg-teal-500/10", text: "text-teal-400", shadow: "shadow-teal-500/5" };

export default createConfigNode({
  componentName: "text_splitter",
  defaultLabel: "Text Splitter",
  accentColor: "teal",
  accentClasses: a,
  handleType: "default",
  handleLabel: "",
  badge: "SPLIT",
  icon: Scissors,
  fields: [
    { key: "strategy", label: "Strategy", placeholder: "character", type: "select", options: ["character", "separator"] },
    { key: "chunk_size", label: "Chunk Size", placeholder: "1000", type: "number" },
    { key: "overlap", label: "Overlap", placeholder: "200", type: "number" },
    { key: "separator", label: "Separator (if separator)", placeholder: "\\n\\n" },
  ],
});
