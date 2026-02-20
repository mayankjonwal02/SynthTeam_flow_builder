import { Search } from "lucide-react"; import { createDBNode } from "./DBNodeFactory";
const a = { border: "border-amber-400", bg: "bg-amber-500/10", text: "text-amber-400", shadow: "shadow-amber-500/5" };
export default createDBNode({ componentName: "sqlite_find", defaultLabel: "SQLite Find", accentColor: "amber", accentClasses: a, opBadge: "SELECT", icon: Search, fields: ["connection_id", "table", "filters"] });
