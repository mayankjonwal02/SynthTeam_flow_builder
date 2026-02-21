"""Autonomous agent component — plans and executes steps dynamically.

Reads LLM config from ai_model handle, tools from ai_tool handles,
memory from ai_memory handle.
"""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.ai.ai_handle_mixin import AIHandleMixin


@register_component("autonomous_agent")
class AutonomousAgentComponent(BaseComponent, AIHandleMixin):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        from app.ai.llm.registry import get_llm
        from app.ai.tools.registry import get_tool, get_tools
        from app.ai.agents.autonomous_agent import run_autonomous_agent
        from app.ai.prompts.template import resolve_prompt_field

        merged: dict = {}
        for output in inputs.values():
            if isinstance(output, dict):
                merged.update(output)

        model_cfg = self.get_model_config(config) or {}
        provider = model_cfg.get("provider") or config.get("provider", "openai")
        model = model_cfg.get("model") or config.get("model", "gpt-4o-mini")
        api_key = model_cfg.get("api_key") or config.get("api_key", "")
        temperature = float(model_cfg.get("temperature") or config.get("temperature", 0.7))

        llm = get_llm(provider=provider, model=model, api_key=api_key, temperature=temperature)

        embed_cfg = self.get_embedding_config(config) or {}
        vs_cfg = self.get_vectorstore_config(config) or {}

        tools = []
        tool_cfgs = self.get_tool_configs(config)
        if tool_cfgs:
            for tc in tool_cfgs:
                tool_name = tc.get("tool_name", "")
                if tool_name:
                    kw = {k: v for k, v in tc.items() if k not in ("__handle_type__", "tool_name")}
                    if tool_name == "knowledge_base":
                        kw = self.enrich_kb_tool_config(kw, embed_cfg, vs_cfg)
                    tools.append(get_tool(tool_name, **kw))
        else:
            tool_names = config.get("tools", [])
            if isinstance(tool_names, str):
                tool_names = [t.strip() for t in tool_names.split(",") if t.strip()]
            if tool_names:
                tools = get_tools(tool_names, config.get("tool_configs", {}))

        system_prompt = resolve_prompt_field(merged, config, "system_prompt", "system_prompt_source")
        goal = resolve_prompt_field(merged, config, "goal", "goal_source") or str(merged.get("input", merged.get("data", "")))
        max_steps = int(config.get("max_steps", config.get("max_iterations", 10)))
        subagent_configs = self.get_subagent_configs(config)

        result = await run_autonomous_agent(
            llm, tools, goal,
            max_steps=max_steps,
            system_prompt=system_prompt or None,
            subagent_configs=subagent_configs,
        )
        return result
