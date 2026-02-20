import { DatabaseZap } from "lucide-react"; import { createDBNode } from "./DBNodeFactory";
const a = { border: "border-amber-400", bg: "bg-amber-500/10", text: "text-amber-400", shadow: "shadow-amber-500/5" };
export default createDBNode({ componentName: "sqlite_insert", defaultLabel: "SQLite Insert", accentColor: "amber", accentClasses: a, opBadge: "INSERT", icon: DatabaseZap, fields: ["connection_id", "table"] });
