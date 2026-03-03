"""Text-to-Speech component.

Reads model/api_key from ai_model handle for the TTS provider.
"""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.ai.ai_handle_mixin import AIHandleMixin


@register_component("text_to_speech")
class TextToSpeechComponent(BaseComponent, AIHandleMixin):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        from app.ai.speech.tts import synthesize
        from app.ai.prompts.template import render_prompt

        merged: dict = {}
        for output in inputs.values():
            if isinstance(output, dict):
                merged.update(output)

        model_cfg = self.get_model_config(config) or {}
        api_key = model_cfg.get("api_key") or config.get("api_key", "")

        text = config.get("text", "") or merged.get("text", "")
        if not text:
            text = render_prompt(config.get("text_template", "{{input}}"), merged)

        result = await synthesize(
            provider=config.get("provider", "openai"),
            text=text,
            api_key=api_key,
            voice=config.get("voice", "alloy"),
            voice_id=config.get("voice_id"),
            model=model_cfg.get("model") or config.get("model"),
        )
        return result
