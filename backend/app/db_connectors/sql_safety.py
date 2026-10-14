"""
SQL safety helpers shared by the SQL connectors and raw-query nodes.

- safe_ident: validates table / column names so request data
  can never be spliced into SQL as an identifier.
- build_bound_query: turns {{input.field}} and :field placeholders in a
  raw query template into driver-specific bound parameters.
"""

import re
from typing import Any, List, Tuple

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# {{input.field}} template placeholders, optionally wrapped in matching quotes
# ('{{input.name}}' was the natural way to write them when values were pasted
# into the SQL; the quotes are dropped because the value is now a parameter)
_TEMPLATE_RE = re.compile(r"(['\"]?)\{\{\s*input\.(\w+)\s*\}\}\1")
# :field named placeholders (not "::type" casts, not inside words like "a:b")
_NAMED_RE = re.compile(r"(?<![:\w]):([A-Za-z_]\w*)")


def safe_ident(name: str) -> str:
    """
    Validate an identifier, optionally schema-qualified ("schema.table").

    Only letters, digits and underscores are allowed, so the name is safe to
    place in SQL unquoted (which keeps each database's normal case folding).
    Raises ValueError for anything else.
    """
    if not isinstance(name, str) or not name:
        raise ValueError("Identifier must be a non-empty string")
    parts = name.split(".")
    if len(parts) > 2 or not all(_IDENT_RE.match(p) for p in parts):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return name


def _placeholder(dialect: str, index: int) -> str:
    if dialect in ("postgres", "supabase"):
        return f"${index}"
    if dialect == "mysql":
        return "%s"
    return "?"


def build_bound_query(template: str, context: dict, dialect: str) -> Tuple[str, List[Any]]:
    """
    Replace {{input.field}} and :field placeholders with bound parameters.

    Values are never inserted into the SQL text. :field is only treated as a
    placeholder when `field` exists in the context, so literals like '10:30'
    and casts like ::text are left alone.
    """
    params: List[Any] = []

    def _bind(key: str) -> str:
        params.append(context.get(key))
        return _placeholder(dialect, len(params))

    query = _TEMPLATE_RE.sub(lambda m: _bind(m.group(2)), template or "")
    query = _NAMED_RE.sub(
        lambda m: _bind(m.group(1)) if m.group(1) in context else m.group(0),
        query,
    )
    return query, params
