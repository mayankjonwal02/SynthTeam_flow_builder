"""Text-to-Speech providers."""

import logging
from typing import Any, Callable, Dict

logger = logging.getLogger("uvicorn.error")

TTS_REGISTRY: Dict[str, Callable] = {}


def register_tts(name: str):
    def decorator(fn):
        TTS_REGISTRY[name] = fn
        logger.info(f"Registered TTS provider: {name}")
        return fn
    return decorator


async def synthesize(provider: str, text: str, api_key: str = "", **kwargs) -> dict:
    fn = TTS_REGISTRY.get(provider)
    if fn is None:
        raise ValueError(f"TTS provider '{provider}' not registered. Available: {list(TTS_REGISTRY.keys())}")
    return await fn(text=text, api_key=api_key, **kwargs)


@register_tts("openai")
async def openai_tts(text: str, api_key: str, **kwargs):
    from openai import AsyncOpenAI
    import base64
    client = AsyncOpenAI(api_key=api_key)
    response = await client.audio.speech.create(
        model=kwargs.get("model", "tts-1"),
        voice=kwargs.get("voice", "alloy"),
        input=text,
    )
    audio_bytes = response.content
    return {"audio_base64": base64.b64encode(audio_bytes).decode(), "format": "mp3"}


@register_tts("elevenlabs")
async def elevenlabs_tts(text: str, api_key: str, **kwargs):
    import base64
    from elevenlabs import AsyncElevenLabs
    client = AsyncElevenLabs(api_key=api_key)
    audio = await client.text_to_speech.convert(
        text=text,
        voice_id=kwargs.get("voice_id", "JBFqnCBsd6RMkjVDRZzb"),
        model_id=kwargs.get("model", "eleven_multilingual_v2"),
    )
    chunks = []
    async for chunk in audio:
        chunks.append(chunk)
    audio_bytes = b"".join(chunks)
    return {"audio_base64": base64.b64encode(audio_bytes).decode(), "format": "mp3"}
