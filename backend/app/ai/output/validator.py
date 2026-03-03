"""Structured output validation — Pydantic and JSON schema support."""

import json
import logging
from typing import Any, Optional

logger = logging.getLogger("uvicorn.error")


def validate_structured_output(
    raw_text: str,
    schema: Optional[dict] = None,
) -> Any:
    """Parse and validate LLM output against a JSON schema.

    If no schema provided, attempts JSON parse and returns as-is.
    """
    if not schema and not raw_text.strip().startswith("{"):
        return {"text": raw_text}

    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM output is not valid JSON: {e}\nRaw: {raw_text[:500]}")

    if schema:
        import jsonschema
        try:
            jsonschema.validate(instance=parsed, schema=schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Output failed schema validation: {e.message}")

    return parsed


def extract_json_from_response(response) -> str:
    """Extract text content from a LangChain AIMessage or string."""
    if hasattr(response, "content"):
        return response.content
    return str(response)
