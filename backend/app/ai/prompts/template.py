"""Prompt template engine with Jinja-style {{input.field}} interpolation."""

import re
from typing import Any


def resolve_prompt_field(context: dict, config: dict, value_key: str, source_key: str = None) -> str:
    """Resolve a prompt field that can be static, from input (one key), or expression (path).
    Config keys: value_key (e.g. 'prompt_template') and source_key (e.g. 'prompt_template_source').
    source_key stores 'static' | 'input' | 'expression'. Defaults to 'static' if source_key missing.
    """
    source = (config.get(source_key or (value_key + "_source")) or "static").strip().lower()
    value = config.get(value_key, "") or ""
    if source == "static":
        return value
    if source == "input":
        return str(context.get(value, ""))
    if source == "expression":
        path = (value or "").strip()
        if not path:
            return ""
        return render_prompt("{{" + path + "}}", context)
    return value


def render_prompt(template: str, context: dict) -> str:
    """Replace {{input.field}} and {{field}} placeholders with context values.

    Supports nested access: {{input.data.name}}, {{user.email}}
    """
    if not template:
        return ""

    def _resolve(path: str, ctx: dict) -> str:
        path = path.strip()
        if path.startswith("input."):
            path = path[6:]

        parts = re.split(r'\.|\[|\]', path)
        parts = [p for p in parts if p]

        result = ctx
        for part in parts:
            if result is None:
                return ""
            try:
                if part.isdigit():
                    result = result[int(part)]
                elif isinstance(result, dict):
                    result = result.get(part)
                else:
                    result = getattr(result, part, None)
            except (KeyError, IndexError, TypeError, AttributeError):
                return ""

        return str(result) if result is not None else ""

    def _replace(match):
        return _resolve(match.group(1), context)

    return re.sub(r"\{\{(.+?)\}\}", _replace, template)


def build_messages(
    system_prompt: str,
    user_prompt: str,
    context: dict,
) -> list:
    """Build a LangChain-compatible message list from templates."""
    from langchain_core.messages import SystemMessage, HumanMessage

    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=render_prompt(system_prompt, context)))
    messages.append(HumanMessage(content=render_prompt(user_prompt, context)))
    return messages
