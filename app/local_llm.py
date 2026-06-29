import httpx
import json
from app.config import get_settings

settings = get_settings()

async def ask_local_llm(user_text: str, system_text: str | None = None):
    """
    Sends a prompt to your local Ollama server and returns the response text.
    Streams NDJSON safely and stitches content together.
    """
    url = f"{settings.OLLAMA_HOST}/api/generate"
    system = system_text or "You are a helpful, concise assistant."
    prompt = f"{system}\n\nUser: {user_text}\nAnswer:"

    payload = {"model": settings.OLLAMA_MODEL, "prompt": prompt}

    reply_parts: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", url, json=payload) as r:
                r.raise_for_status()
                async for chunk in r.aiter_text():
                    if not chunk:
                        continue
                    for line in chunk.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                            piece = obj.get("response", "")
                            if piece:
                                reply_parts.append(piece)
                        except json.JSONDecodeError:
                            continue
        
        reply = "".join(reply_parts).strip()
        return reply or "[Local AI Error: empty response]"
    except httpx.HTTPStatusError as e:
        return f"[Local AI Error: HTTP {e.response.status_code} from ollama]"
    except Exception as e:
        return f"[Local AI Error: {e}]"

    

# async def ask_local_llm(prompt: str) -> str :
#     """
#     Sends a prompt to your local Ollama model and returns the text reply.
#     """
#     try:
#         url = "http://localhost:11434/api/generate"
#         payload = {"model": "phi", "prompt" : prompt}
#         async with httpx.AsyncClient(timeout=60) as client:
#             async with client.stream("POST", url, json=payload) as response:
#                 reply = ""
#                 async for chunk in response.aiter_text():
#                     if chunk.strip():
#                         try:
#                             data = json.loads(chunk)
#                             reply += data.get("response", "")
#                         except json.JSONDecodeError:
#                             continue
#         return reply.strip()
#     except Exception as e:
#         return f"[Local AI Error: {e}]"