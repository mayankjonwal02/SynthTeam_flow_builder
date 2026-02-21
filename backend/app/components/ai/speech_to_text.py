"""Speech-to-Text component.

Reads model/api_key from ai_model handle for the STT provider.
"""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.ai.ai_handle_mixin import AIHandleMixin


@register_component("speech_to_text")
class SpeechToTextComponent(BaseComponent, AIHandleMixin):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        from app.ai.speech.stt import transcribe

        merged: dict = {}
        for output in inputs.values():
            if isinstance(output, dict):
                merged.update(output)

        model_cfg = self.get_model_config(config) or {}
        api_key = model_cfg.get("api_key") or config.get("api_key", "")

        audio_input = config.get("audio_path", "") or merged.get("audio_path", "") or merged.get("audio_url", "")

        result = await transcribe(
            provider=config.get("provider", "openai_whisper"),
            audio_input=audio_input,
            api_key=api_key,
            language=config.get("language"),
        )
        return result
