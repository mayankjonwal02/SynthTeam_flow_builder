import { PenLine } from "lucide-react"; import { createDBNode } from "./DBNodeFactory";
const a = { border: "border-emerald-400", bg: "bg-emerald-500/10", text: "text-emerald-400", shadow: "shadow-emerald-500/5" };
export default createDBNode({ componentName: "supa_update", defaultLabel: "Supa Update", accentColor: "emerald", accentClasses: a, opBadge: "UPDATE", icon: PenLine, fields: ["connection_id", "table", "filters"] });
