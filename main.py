from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from typing import Any, Optional
import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory

from config import settings
from schemas import GenerateRequest, GenerateResponse, StructuredRequest, StructuredResponse

app = FastAPI(title="Gemini REST Router", version="1.0.0")

# Allow CORS for all origins (customize as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=settings.GEMINI_API_KEY)

def get_model(model_name: str = None):
    return genai.GenerativeModel(model_name or settings.DEFAULT_MODEL)

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if not settings.API_KEY:
        # If no API key is set in config, allow all (for dev)
        return
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")

@app.get("/v1/health")
def health():
    try:
        # Simple health check: try to instantiate the model
        _ = get_model()
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(e)})

@app.post("/v1/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest, api_key: Any = Depends(verify_api_key)):
    try:
        model = get_model(req.model)
        gen_config = {
            "temperature": req.temperature or settings.DEFAULT_TEMPERATURE,
        }
        if req.max_tokens:
            gen_config["max_output_tokens"] = req.max_tokens
        if req.extra:
            gen_config.update(req.extra)
        # Generate response
        response = await model.generate_content_async(
            req.prompt,
            generation_config=gen_config
        )
        content = response.text if hasattr(response, "text") else str(response)
        usage = getattr(response, "usage_metadata", None)
        metadata = {"model": model.model_name, "provider": "gemini"}
        return GenerateResponse(content=content, usage=usage, metadata=metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini error: {e}")

@app.post("/v1/structured", response_model=StructuredResponse)
async def structured(req: StructuredRequest, api_key: Any = Depends(verify_api_key)):
    try:
        model = get_model(req.model)
        gen_config = {
            "temperature": req.temperature or settings.DEFAULT_TEMPERATURE,
        }
        if req.max_tokens:
            gen_config["max_output_tokens"] = req.max_tokens
        if req.extra:
            gen_config.update(req.extra)
        # Generate structured response
        prompt = req.prompt
        schema = req.schema
        # For Gemini, we use function calling or JSON mode if available; here, just return text for now
        response = await model.generate_content_async(
            prompt,
            generation_config=gen_config
        )
        content = response.text if hasattr(response, "text") else str(response)
        # Try to parse JSON from the response
        import json
        try:
            result = json.loads(content)
        except Exception:
            result = {"raw": content}
        usage = getattr(response, "usage_metadata", None)
        metadata = {"model": model.model_name, "provider": "gemini"}
        return StructuredResponse(result=result, usage=usage, metadata=metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini error: {e}") 