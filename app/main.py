from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import ChatRequest, ChatResponse
from app.config import get_settings
from app.local_llm import ask_local_llm
# from app.llm import ask_llm
import traceback
import os
import httpx


settings = get_settings()
app = FastAPI(title="Shadrach Chatbot API", version="0.1.0")

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# CORS for local dev or future web client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": settings.OPENAI_MODEL,
        "has_key": bool(settings.OPENAI_API_KEY),
        "env": settings.APP_ENV,
    }

@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    return {"error": "Verification failed"}

from app.local_llm import ask_local_llm  # new import

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    msg = (req.message or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Empty message")

     # 1) Retrieve relevant chunks
    docs = retrieve(msg, k=4)
    context = build_context(docs) if docs else ""

    # 2) Build a grounded prompt
    system = req.system or "You are a WhatsApp chatbot for the Council Complaint Reporting and Service Management System."
    prompt = (
        f"{system}\n\n"
        f"Answer the user's question clearly and briefly."
        f"Use 1–2 sentences only."
        f"Do NOT mention documents, files, or sources."
        f"Do NOT repeat the context."
        f"Do NOT explain system details unless asked."
        f"Be polite, neutral, and user-friendly."
        f"Answer apprioprately when the user asks for help, greetings, or small talk.\n"
        f"When a user wants to make a complaint, guide them through the process clearly and patiently.\n"
        f"Only say you don't know if the context is completely unrelated.\n\n"
        f"Context:\n{context}\n\n"
        f"User: {msg}\n"
        f"Answer:"
    )

    # 3) Ask the local model
    reply = await ask_local_llm(prompt)
    if not reply:
        raise HTTPException(status_code=500, detail="Empty reply from local model")

    return ChatResponse(reply=reply, model="phi (local)")
    


from app.rag import index_folder, retrieve, build_context
@app.post("/index")
def index_docs():
    files, chunks = index_folder()
    return {"indexed_files": files, "chunks": chunks}

@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    print("Incoming webhook:", data)

    # 1️⃣ Check if this is a WhatsApp message event
    if "entry" not in data:
        return {"status": "ignored"}

    try:
        entry = data["entry"][0]
        changes = entry.get("changes", [])
        if not changes:
            return {"status": "no changes"}

        value = changes[0].get("value", {})

        # Ignore delivery/read status updates
        if "messages" not in value:
            return {"status": "not a message event"}

        message = value["messages"][0]

        if message["type"] != "text":
            return {"status": "non-text message ignored"}

        user_number = message["from"]
        user_text = message["text"]["body"]

        print("User:", user_text)

        # ---- RAG ----
        docs = retrieve(user_text, k=6)
        context = build_context(docs) if docs else ""

        if not context:
            reply = "I couldn't find relevant information in the knowledge base."
        else:
            prompt = f"""
You are a professional assistant.
Answer clearly and concisely.

Context:
{context}

Question:
{user_text}

Answer:
"""
            reply = await ask_local_llm(prompt)

        await send_whatsapp_message(user_number, reply)

    except Exception as e:
        print("Webhook processing error:", e)

    return {"status": "ok"}


async def send_whatsapp_message(to: str, text: str):
    url = f"https://graph.facebook.com/v18.0/{PHONE_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }

    async with httpx.AsyncClient() as client:
        await client.post(url, headers=headers, json=payload)




# @app.post("/chat", response_model=ChatResponse)
# def chat(req: ChatRequest):
#     msg = (req.message or "").strip()
#     if not msg:
#         raise HTTPException(status_code=400, detail="Empty message")
    
#     try:
#         reply, usage = ask_llm(msg, req.system)
#         return ChatResponse(
#             reply=reply,
#             model=settings.OPENAI_MODEL,
#             tokens_in=usage.get("prompt_tokens"),
#             tokens_out=usage.get("completion_tokens"),
#         )
#     except Exception as e:
#         traceback.print_exc()
#         if settings.APP_ENV.lower() == "dev":
#             raise HTTPException(status_code=500, detail=f"LLM failed: {e}")
#         raise HTTPException(status_code=500, detail="LLM request failed")

