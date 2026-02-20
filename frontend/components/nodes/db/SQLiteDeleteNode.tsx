import { Trash } from "lucide-react"; import { createDBNode } from "./DBNodeFactory";
const a = { border: "border-amber-400", bg: "bg-amber-500/10", text: "text-amber-400", shadow: "shadow-amber-500/5" };
export default createDBNode({ componentName: "sqlite_delete", defaultLabel: "SQLite Delete", accentColor: "amber", accentClasses: a, opBadge: "DELETE", icon: Trash, fields: ["connection_id", "table", "filters"] });
