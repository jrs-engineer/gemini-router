# Gemini FastAPI Router

A lightweight REST API proxy for Google Gemini, designed for secure, remote LLM access from your main application.

## Features
- REST endpoints for text and structured generation
- API key protection (via `X-API-KEY` header)
- Health check endpoint
- Easy deployment (FastAPI + Uvicorn)

## Setup

1. **Clone or copy this folder to your server.**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Create a `.env` file:**
   Copy `.env.example` to `.env` and fill in your keys:
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```
   - `GEMINI_API_KEY`: Your Google Gemini API key (required)
   - `ROUTER_API_KEY`: Secret key for protecting the router (required for production)
   - `GEMINI_MODEL`, `GEMINI_TEMPERATURE`: (optional) Defaults for Gemini

4. **Run the server:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## Endpoints

- `GET /v1/health` — Health check (no auth required)
- `POST /v1/generate` — Text generation (requires `X-API-KEY`)
- `POST /v1/structured` — Structured (JSON) generation (requires `X-API-KEY`)

## Example Request

```bash
curl -X POST http://localhost:8000/v1/generate \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your_router_secret_key_here" \
  -d '{"prompt": "Tell me a joke about Python."}'
```

## Security
- All endpoints except `/v1/health` require the `X-API-KEY` header.
- Never expose your Gemini API key to clients—only to this router.

## Customization
- You can add logging, request limits, or more endpoints as needed.

## License
MIT 