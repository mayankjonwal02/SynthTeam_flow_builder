import { FileJson } from "lucide-react";
import { createConfigNode } from "./ConfigNodeFactory";

const a = { border: "border-emerald-400", bg: "bg-emerald-500/10", text: "text-emerald-400", shadow: "shadow-emerald-500/5" };

export default createConfigNode({
  componentName: "output_structure",
  defaultLabel: "Output Structure",
  accentColor: "emerald",
  accentClasses: a,
  handleType: "ai_structure",
  handleLabel: "Schema",
  badge: "SCHEMA",
  icon: FileJson,
  fields: [
    { key: "schema", label: "JSON Schema", placeholder: '{"type":"object","properties":{...}}', type: "textarea" },
  ],
});
