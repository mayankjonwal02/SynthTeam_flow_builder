import { Mail } from "lucide-react";
import { createConfigNode } from "./ConfigNodeFactory";

const a = { border: "border-amber-400", bg: "bg-amber-500/10", text: "text-amber-400", shadow: "shadow-amber-500/5" };

export default createConfigNode({
  componentName: "tool_email",
  defaultLabel: "Email Sender",
  accentColor: "amber",
  accentClasses: a,
  handleType: "ai_tool",
  handleLabel: "Tool",
  badge: "TOOL",
  icon: Mail,
  fields: [
    { key: "smtp_host", label: "SMTP Host", placeholder: "smtp.gmail.com" },
    { key: "smtp_port", label: "SMTP Port", placeholder: "587", type: "number" },
    { key: "username", label: "Username", placeholder: "user@example.com" },
    { key: "password", label: "Password", placeholder: "...", type: "password" },
    { key: "from_email", label: "From Email", placeholder: "user@example.com" },
  ],
});
