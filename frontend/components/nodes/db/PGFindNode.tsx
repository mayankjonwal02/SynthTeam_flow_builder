import { Search } from "lucide-react"; import { createDBNode } from "./DBNodeFactory";
const a = { border: "border-blue-400", bg: "bg-blue-500/10", text: "text-blue-400", shadow: "shadow-blue-500/5" };
export default createDBNode({ componentName: "pg_find", defaultLabel: "PG Find", accentColor: "blue", accentClasses: a, opBadge: "SELECT", icon: Search, fields: ["connection_id", "table", "filters"] });
