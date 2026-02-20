import { Search } from "lucide-react"; import { createDBNode } from "./DBNodeFactory";
const a = { border: "border-emerald-400", bg: "bg-emerald-500/10", text: "text-emerald-400", shadow: "shadow-emerald-500/5" };
export default createDBNode({ componentName: "supa_find", defaultLabel: "Supa Find", accentColor: "emerald", accentClasses: a, opBadge: "SELECT", icon: Search, fields: ["connection_id", "table", "filters"] });
