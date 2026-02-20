import { DatabaseZap } from "lucide-react"; import { createDBNode } from "./DBNodeFactory";
const a = { border: "border-emerald-400", bg: "bg-emerald-500/10", text: "text-emerald-400", shadow: "shadow-emerald-500/5" };
export default createDBNode({ componentName: "supa_insert", defaultLabel: "Supa Insert", accentColor: "emerald", accentClasses: a, opBadge: "INSERT", icon: DatabaseZap, fields: ["connection_id", "table"] });
