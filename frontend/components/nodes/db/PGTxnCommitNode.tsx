import { CheckCircle } from "lucide-react"; import { createDBNode } from "./DBNodeFactory";
const a = { border: "border-blue-400", bg: "bg-blue-500/10", text: "text-blue-400", shadow: "shadow-blue-500/5" };
export default createDBNode({ componentName: "pg_txn_commit", defaultLabel: "PG Txn Commit", accentColor: "blue", accentClasses: a, opBadge: "COMMIT", icon: CheckCircle, fields: ["connection_id"] });
