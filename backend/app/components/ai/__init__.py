"""AI / Agent components — each mirrors a frontend ReactFlow AI node type."""

# ── Config nodes (typed handle outputs) ──────────────────────────────
import app.components.ai.llm_model           # noqa: F401
import app.components.ai.output_structure     # noqa: F401
import app.components.ai.memory_config        # noqa: F401
import app.components.ai.embedding_model      # noqa: F401
import app.components.ai.vectorstore_config   # noqa: F401

# ── Tool nodes (ai_tool handle outputs) ──────────────────────────────
import app.components.ai.tool_web_search      # noqa: F401
import app.components.ai.tool_http_request    # noqa: F401
import app.components.ai.tool_calculator      # noqa: F401
import app.components.ai.tool_db_query        # noqa: F401
import app.components.ai.tool_code_executor   # noqa: F401
import app.components.ai.tool_file_ops        # noqa: F401
import app.components.ai.tool_email           # noqa: F401
import app.components.ai.tool_gmail            # noqa: F401
import app.components.ai.tool_slack           # noqa: F401
import app.components.ai.tool_workflow        # noqa: F401
import app.components.ai.tool_composio        # noqa: F401
import app.components.ai.tool_knowledge_base  # noqa: F401

# ── RAG pipeline nodes ───────────────────────────────────────────────
import app.components.ai.doc_loader           # noqa: F401
import app.components.ai.text_splitter        # noqa: F401

# ── Execution nodes (consume typed handles) ──────────────────────────
import app.components.ai.llm_call             # noqa: F401
import app.components.ai.embedding_generate   # noqa: F401
import app.components.ai.vector_upsert        # noqa: F401
import app.components.ai.vector_search        # noqa: F401
import app.components.ai.vector_delete        # noqa: F401
import app.components.ai.retrieval            # noqa: F401
import app.components.ai.agent_run            # noqa: F401
import app.components.ai.autonomous_agent     # noqa: F401
import app.components.ai.vision_analyze       # noqa: F401
import app.components.ai.speech_to_text       # noqa: F401
import app.components.ai.text_to_speech       # noqa: F401
