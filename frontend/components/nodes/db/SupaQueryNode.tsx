import { TerminalSquare } from "lucide-react"; import { createDBNode } from "./DBNodeFactory";
const a = { border: "border-emerald-400", bg: "bg-emerald-500/10", text: "text-emerald-400", shadow: "shadow-emerald-500/5" };
export default createDBNode({ componentName: "supa_raw_query", defaultLabel: "Supa Query", accentColor: "emerald", accentClasses: a, opBadge: "SQL", icon: TerminalSquare, fields: ["connection_id", "query"] });
