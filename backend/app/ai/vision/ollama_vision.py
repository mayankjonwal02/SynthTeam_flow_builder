from app.ai.vision.registry import register_vision_provider
from app.core.config import settings


@register_vision_provider("ollama")
async def ollama_vision(image_input: str, prompt: str, api_key: str = "", **kwargs):
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage

    llm = ChatOllama(model=kwargs.get("model", "llava"), base_url=kwargs.get("base_url") or settings.OLLAMA_BASE_URL)
    content = [{"type": "text", "text": prompt}]

    if image_input.startswith("http"):
        content.append({"type": "image_url", "image_url": {"url": image_input}})
    else:
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_input}"}})

    msg = HumanMessage(content=content)
    response = await llm.ainvoke([msg])
    return {"analysis": response.content}
