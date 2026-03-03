import { Eye } from "lucide-react";
import { createAIExecNode } from "./AIExecNodeFactory";

const a = { border: "border-cyan-400", bg: "bg-cyan-500/10", text: "text-cyan-400", shadow: "shadow-cyan-500/5" };

export default createAIExecNode({
  componentName: "vision_analyze",
  defaultLabel: "Vision Analyze",
  accentColor: "cyan",
  accentClasses: a,
  badge: "VISION",
  icon: Eye,
  targetHandles: [
    { id: "ai_model", label: "Model", color: "purple" },
  ],
  fields: [
    { key: "image_url", label: "Image URL / Base64", placeholder: "https://... or base64" },
    { key: "prompt", label: "Prompt", placeholder: "Describe this image.", type: "textarea" },
  ],
});
