"""LLM Call component — multi-provider LLM invocation with optional structured output.

Reads LLM config from ai_model handle, output schema from ai_structure handle.
Falls back to inline config fields for backward compatibility.
"""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.ai.ai_handle_mixin import AIHandleMixin


@register_component("llm_call")
class LLMCallComponent(BaseComponent, AIHandleMixin):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        from app.ai.llm.registry import get_llm
        from app.ai.prompts.template import build_messages, resolve_prompt_field
        from app.ai.output.validator import validate_structured_output, extract_json_from_response
        from app.ai.observability.tracker import AITracker, extract_token_usage

        merged: dict = {}
        for output in inputs.values():
            if isinstance(output, dict):
                merged.update(output)

        model_cfg = self.get_model_config(config) or {}
        provider = model_cfg.get("provider") or config.get("provider", "openai")
        model = model_cfg.get("model") or config.get("model", "gpt-4o-mini")
        api_key = model_cfg.get("api_key") or config.get("api_key", "")
        temperature = float(model_cfg.get("temperature") or config.get("temperature", 0.7))

        tracker = AITracker("", "llm_call")
        tracker.set_model(provider, model)
        tracker.start()

        llm = get_llm(
            provider=provider,
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=model_cfg.get("max_tokens") or config.get("max_tokens"),
            base_url=model_cfg.get("base_url") or config.get("base_url"),
        )

        system_prompt = resolve_prompt_field(merged, config, "system_prompt", "system_prompt_source")
        user_prompt = resolve_prompt_field(merged, config, "prompt_template", "prompt_template_source") or "{{input}}"
        messages = build_messages(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            context=merged,
        )

        response = await llm.ainvoke(messages)
        tracker.stop()

        token_usage = extract_token_usage(response)
        if token_usage:
            tracker.set_tokens(token_usage.get("prompt", 0), token_usage.get("completion", 0))

        raw_text = extract_json_from_response(response)

        struct_cfg = self.get_structure_config(config)
        schema = (struct_cfg or {}).get("schema") or config.get("structured_output_schema")
        if schema:
            parsed = validate_structured_output(raw_text, schema)
            return {"output": parsed, **tracker.to_dict()}

        return {"output": raw_text, **tracker.to_dict()}
