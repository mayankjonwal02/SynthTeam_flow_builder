"""AI & Agent layer — auto-registers all providers, tools, and stores on import."""

import app.ai.llm          # noqa: F401
import app.ai.embeddings   # noqa: F401
import app.ai.vectorstores # noqa: F401
import app.ai.tools        # noqa: F401
import app.ai.vision       # noqa: F401
