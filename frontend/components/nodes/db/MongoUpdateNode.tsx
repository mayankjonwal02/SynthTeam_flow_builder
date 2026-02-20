import { PenLine } from "lucide-react"; import { createDBNode } from "./DBNodeFactory";
const a = { border: "border-green-400", bg: "bg-green-500/10", text: "text-green-400", shadow: "shadow-green-500/5" };
export default createDBNode({ componentName: "mongo_update", defaultLabel: "Mongo Update", accentColor: "green", accentClasses: a, opBadge: "UPDATE", icon: PenLine, fields: ["connection_id", "database", "collection", "filter"] });
