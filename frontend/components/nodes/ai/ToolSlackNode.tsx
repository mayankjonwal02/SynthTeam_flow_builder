import { MessageSquare } from "lucide-react";
import { createConfigNode } from "./ConfigNodeFactory";

const a = { border: "border-amber-400", bg: "bg-amber-500/10", text: "text-amber-400", shadow: "shadow-amber-500/5" };

export default createConfigNode({
  componentName: "tool_slack",
  defaultLabel: "Slack Notifier",
  accentColor: "amber",
  accentClasses: a,
  handleType: "ai_tool",
  handleLabel: "Tool",
  badge: "TOOL",
  icon: MessageSquare,
  fields: [
    { key: "webhook_url", label: "Webhook URL", placeholder: "https://hooks.slack.com/..." },
  ],
});
