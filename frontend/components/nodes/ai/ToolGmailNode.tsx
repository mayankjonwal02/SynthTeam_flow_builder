import { Mail } from "lucide-react";
import { createConfigNode } from "./ConfigNodeFactory";

const a = { border: "border-red-400", bg: "bg-red-500/10", text: "text-red-400", shadow: "shadow-red-500/5" };

export default createConfigNode({
  componentName: "tool_gmail",
  defaultLabel: "Gmail",
  accentColor: "red",
  accentClasses: a,
  handleType: "ai_tool",
  handleLabel: "Tool",
  badge: "TOOL",
  icon: Mail,
  fields: [
    { key: "email", label: "Gmail address", placeholder: "you@gmail.com" },
    { key: "app_password", label: "App password", placeholder: "16-character app password", type: "password" },
  ],
});
