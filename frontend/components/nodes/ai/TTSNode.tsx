import { Volume2 } from "lucide-react";
import { createAIExecNode } from "./AIExecNodeFactory";

const a = { border: "border-cyan-400", bg: "bg-cyan-500/10", text: "text-cyan-400", shadow: "shadow-cyan-500/5" };

export default createAIExecNode({
  componentName: "text_to_speech",
  defaultLabel: "Text to Speech",
  accentColor: "cyan",
  accentClasses: a,
  badge: "TTS",
  icon: Volume2,
  targetHandles: [
    { id: "ai_model", label: "Model", color: "purple" },
  ],
  fields: [
    { key: "provider", label: "Provider", placeholder: "openai" },
    { key: "voice", label: "Voice", placeholder: "alloy" },
    { key: "text_template", label: "Text Template", placeholder: "{{input}}", type: "textarea" },
  ],
});
