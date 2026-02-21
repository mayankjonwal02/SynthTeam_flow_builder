"""Agent Run component — ReAct agent execution.

Reads LLM config from ai_model handle, tools from ai_tool handles,
memory from ai_memory handle, structure from ai_structure handle,
sub-agents from ai_subagent handles.
"""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.ai.ai_handle_mixin import AIHandleMixin


@register_component("agent_run")
class AgentRunComponent(BaseComponent, AIHandleMixin):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        from app.ai.llm.registry import get_llm
        from app.ai.tools.registry import get_tool
        from app.ai.agents.react_agent import run_react_agent
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
            from app.ai.tools.registry import get_tools
            tool_names = config.get("tools", [])
            if isinstance(tool_names, str):
                tool_names = [t.strip() for t in tool_names.split(",") if t.strip()]
            if tool_names:
                tools = get_tools(tool_names, config.get("tool_configs", {}))

        user_input = resolve_prompt_field(merged, config, "prompt_template", "prompt_template_source") or resolve_prompt_field(merged, config, "prompt", "prompt_source") or str(merged.get("input", merged.get("data", "")))
        system_prompt = resolve_prompt_field(merged, config, "system_prompt", "system_prompt_source")
        max_iter = int(config.get("max_iterations", 10))

        previous_messages: list = []
        memory = None
        session_key = "default"
        mem_cfg = self.get_memory_config(config)
        if mem_cfg:
            from app.ai.memory.manager import MemoryManager
            from app.ai.agents.react_agent import _message_to_dict
            backend = mem_cfg.get("backend", "in_memory")
            session_key = (
                request_data.get("session_id")
                or mem_cfg.get("session_id")
                or "default"
            )
            memory = MemoryManager.create(
                backend=backend,
                redis_url=mem_cfg.get("redis_url", ""),
            )
            raw = await memory.get(session_key, limit=mem_cfg.get("max_messages", 50))
            previous_messages = [m for m in raw if isinstance(m, dict) and m.get("role") and m.get("content") is not None]

        result = await run_react_agent(
            llm, tools, user_input,
            max_iterations=max_iter,
            system_prompt=system_prompt or None,
            previous_messages=previous_messages if previous_messages else None,
        )

        if memory and result.get("messages"):
            from app.ai.agents.react_agent import _message_to_dict
            await memory.add(session_key, {"role": "user", "content": user_input})
            num_input = len(previous_messages) + (1 if system_prompt else 0) + 1
            for msg in result["messages"][num_input:]:
                await memory.add(session_key, _message_to_dict(msg))

        return {k: v for k, v in result.items() if k != "messages"}
