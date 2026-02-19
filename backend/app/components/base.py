"""
Abstract base class for all pipeline components.

Every component follows the same contract:
  - Receives `request_data` (the original HTTP request body)
  - Receives `inputs` — a dict mapping parent-node IDs to their outputs
  - Receives `config` — the node's own configuration from the graph JSON
  - Returns an output dict that becomes available to downstream nodes
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseComponent(ABC):

    @abstractmethod
    async def execute(
        self,
        request_data: dict,
        inputs: Dict[str, Any],
        config: dict,
    ) -> Any:
        """
        Run this component's logic.

        Args:
            request_data: The raw HTTP request body that entered the pipeline.
            inputs:       Outputs of all parent nodes keyed by their node-id.
            config:       This node's configuration from the graph JSON.

        Returns:
            Arbitrary data that will be stored in the execution context and
            made available to downstream nodes.
        """
        ...
