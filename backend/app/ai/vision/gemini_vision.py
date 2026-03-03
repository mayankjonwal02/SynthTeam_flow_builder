from app.ai.vision.registry import register_vision_provider


@register_vision_provider("gemini")
async def gemini_vision(image_input: str, prompt: str, api_key: str, **kwargs):
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage

    llm = ChatGoogleGenerativeAI(model=kwargs.get("model", "gemini-2.0-flash"), google_api_key=api_key)
    content = [{"type": "text", "text": prompt}]

    if image_input.startswith("http"):
        content.append({"type": "image_url", "image_url": {"url": image_input}})
    else:
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_input}"}})

    msg = HumanMessage(content=content)
    response = await llm.ainvoke([msg])
    return {"analysis": response.content}
