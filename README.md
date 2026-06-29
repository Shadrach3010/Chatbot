# Shadrach Chatbot API

A production-ready conversational assistant built with FastAPI, Retrieval-Augmented Generation (RAG), and a local Ollama language model. This project is designed to provide grounded, policy-aware responses for complaint reporting workflows and can also be connected to WhatsApp through webhooks.

## Overview

This chatbot combines:

- A FastAPI backend for REST and webhook endpoints
- A local LLM powered by Ollama (default model: `phi`)
- Chroma vector search for document retrieval from a knowledge base
- A complaint-handling assistant style tuned for service and complaint workflows

The system retrieves relevant content from stored documents, injects it into the prompt, and responds with concise, grounded answers.

## Key Features

- REST chat API with system prompt customization
- RAG-based retrieval over local documents
- WhatsApp webhook integration for inbound messaging
- Health check endpoint for monitoring
- Local inference via Ollama for privacy-friendly deployments
- Easy knowledge-base indexing for new documentation

## Project Structure

```text
.
├── app/
│   ├── config.py          # Environment and settings management
│   ├── llm.py             # OpenAI-based LLM wrapper (optional)
│   ├── local_llm.py       # Ollama integration for local generation
│   ├── main.py            # FastAPI application and routes
│   ├── rag.py             # Document loading, chunking, indexing, and retrieval
│   └── schemas.py         # Pydantic request/response models
├── data/
│   ├── docs/              # Source documents for indexing
│   └── chroma/            # Persistent Chroma vector database
└── requirements.txt       # Python dependencies
```

## Prerequisites

Before running the project, make sure you have:

- Python 3.10+
- Ollama installed and running locally
- A WhatsApp Business API setup (optional, for webhook messaging)

## Installation

1. Clone the repository
2. Create and activate a virtual environment
3. Install dependencies
4. Start Ollama and pull the desired model

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ollama serve
ollama pull phi
```

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
ollama serve
ollama pull phi
```

## Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
APP_ENV=dev
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=phi

# Optional WhatsApp webhook configuration
WHATSAPP_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_ID=your_phone_id
VERIFY_TOKEN=your_verify_token

# Optional OpenAI fallback (currently commented in the app)
# OPENAI_API_KEY=your_openai_key
# OPENAI_MODEL=gpt-4o-mini
```

> Replace the placeholder values with your actual credentials before production use.

## Running the Server

Start the API locally:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- http://localhost:8000/docs for Swagger UI
- http://localhost:8000/redoc for ReDoc

## Core API Endpoints

### Health Check

```bash
GET /health
```

Returns application status, model metadata, and environment info.

### Chat

```bash
POST /chat
```

Body example:

```json
{
  "message": "How do I file a complaint?",
  "system": "You are a helpful complaint support assistant."
}
```

### Index Documents

```bash
POST /index
```

Indexes all `.txt` and `.md` documents located in `data/docs` and stores embeddings in the Chroma database.

### WhatsApp Webhook Verification

```bash
GET /webhook
```

Used by Meta to verify the WhatsApp webhook callback URL.

### Incoming WhatsApp Messages

```bash
POST /webhook
```

Processes inbound WhatsApp text messages, retrieves relevant context, and sends a response back to the user.

## Document Indexing Workflow

1. Add or update source content in `data/docs`
2. Trigger the index endpoint:

```bash
curl -X POST http://localhost:8000/index
```

3. Send a chat query:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is the complaint escalation procedure?"}'
```

## WhatsApp Integration

To test WhatsApp webhook integration locally:

1. Start the app locally.
2. Expose the local server using a tool such as `ngrok`.
3. Configure your WhatsApp webhook callback URL to point to:

```text
https://<your-public-url>/webhook
```

4. Use the same `VERIFY_TOKEN` value in both your app configuration and the WhatsApp dashboard.

## Troubleshooting

### Ollama is not responding

Make sure the local server is running:

```bash
ollama serve
```

Check the configured model is available:

```bash
ollama list
```

### No relevant answers are being returned

- Verify that documents exist in `data/docs`
- Re-index the knowledge base with `POST /index`
- Confirm that `OLLAMA_HOST` points to the correct local server address

### Import or dependency errors

Reinstall dependencies:

```bash
pip install -r requirements.txt
```

## Future Enhancements

- Add authentication for admin and API access
- Support PDF parsing for uploaded knowledge sources
- Add analytics and conversation logging
- Support multilingual responses
- Enable fallback to OpenAI when local inference is unavailable

## License

This project does not currently include a license file. If you plan to distribute it publicly, add an appropriate license such as MIT or Apache-2.0.
