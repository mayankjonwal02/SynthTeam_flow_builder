"""Base class for SynthTeam tools — wraps LangChain BaseTool."""

from langchain_core.tools import BaseTool as LCBaseTool
from typing import Any


class SynthTool(LCBaseTool):
    """All SynthTeam tools extend this for consistent interface."""

    class Config:
        arbitrary_types_allowed = True
