"""Speech-to-Text providers."""

import logging
from typing import Any, Callable, Dict

logger = logging.getLogger("uvicorn.error")

STT_REGISTRY: Dict[str, Callable] = {}


def register_stt(name: str):
    def decorator(fn):
        STT_REGISTRY[name] = fn
        logger.info(f"Registered STT provider: {name}")
        return fn
    return decorator


async def transcribe(provider: str, audio_input: str, api_key: str = "", **kwargs) -> dict:
    fn = STT_REGISTRY.get(provider)
    if fn is None:
        raise ValueError(f"STT provider '{provider}' not registered. Available: {list(STT_REGISTRY.keys())}")
    return await fn(audio_input=audio_input, api_key=api_key, **kwargs)


@register_stt("openai_whisper")
async def openai_whisper(audio_input: str, api_key: str, **kwargs):
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=api_key)
    with open(audio_input, "rb") as f:
        transcript = await client.audio.transcriptions.create(
            model="whisper-1", file=f,
            language=kwargs.get("language"),
        )
    return {"text": transcript.text}


@register_stt("deepgram")
async def deepgram_stt(audio_input: str, api_key: str, **kwargs):
    from deepgram import DeepgramClient, PrerecordedOptions, FileSource
    client = DeepgramClient(api_key)
    with open(audio_input, "rb") as f:
        buffer = f.read()
    payload: FileSource = {"buffer": buffer}
    options = PrerecordedOptions(model="nova-2", smart_format=True)
    response = await client.listen.asyncrest.v("1").transcribe_file(payload, options)
    text = response.results.channels[0].alternatives[0].transcript
    return {"text": text}
