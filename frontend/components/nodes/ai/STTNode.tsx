import { Mic } from "lucide-react";
import { createAIExecNode } from "./AIExecNodeFactory";

const a = { border: "border-cyan-400", bg: "bg-cyan-500/10", text: "text-cyan-400", shadow: "shadow-cyan-500/5" };

export default createAIExecNode({
  componentName: "speech_to_text",
  defaultLabel: "Speech to Text",
  accentColor: "cyan",
  accentClasses: a,
  badge: "STT",
  icon: Mic,
  targetHandles: [
    { id: "ai_model", label: "Model", color: "purple" },
  ],
  fields: [
    { key: "provider", label: "Provider", placeholder: "openai_whisper" },
    { key: "audio_path", label: "Audio Path", placeholder: "/path/to/audio.wav" },
    { key: "language", label: "Language (optional)", placeholder: "en" },
  ],
});
