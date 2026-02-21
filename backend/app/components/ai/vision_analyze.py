"""Vision analysis component.

Reads LLM/model config from ai_model handle for provider/api_key.
"""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.ai.ai_handle_mixin import AIHandleMixin


@register_component("vision_analyze")
class VisionAnalyzeComponent(BaseComponent, AIHandleMixin):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        from app.ai.vision.registry import analyze_image
        from app.ai.prompts.template import render_prompt

        merged: dict = {}
        for output in inputs.values():
            if isinstance(output, dict):
                merged.update(output)

        model_cfg = self.get_model_config(config) or {}
        provider = model_cfg.get("provider") or config.get("provider", "openai")
        api_key = model_cfg.get("api_key") or config.get("api_key", "")
        model = model_cfg.get("model") or config.get("model")

        image_input = config.get("image_url", "") or merged.get("image_url", "") or merged.get("image_base64", "")
        prompt = render_prompt(config.get("prompt", "Describe this image in detail."), merged)

        result = await analyze_image(
            provider=provider,
            image_input=image_input,
            prompt=prompt,
            api_key=api_key,
            model=model,
            base_url=model_cfg.get("base_url") or config.get("base_url"),
        )
        return result
