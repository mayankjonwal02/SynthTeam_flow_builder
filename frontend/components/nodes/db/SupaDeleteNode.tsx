import { Trash } from "lucide-react"; import { createDBNode } from "./DBNodeFactory";
const a = { border: "border-emerald-400", bg: "bg-emerald-500/10", text: "text-emerald-400", shadow: "shadow-emerald-500/5" };
export default createDBNode({ componentName: "supa_delete", defaultLabel: "Supa Delete", accentColor: "emerald", accentClasses: a, opBadge: "DELETE", icon: Trash, fields: ["connection_id", "table", "filters"] });
