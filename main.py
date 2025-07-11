from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from typing import Any, Optional
import asyncio
from google.generativeai.client import configure
from google.generativeai.generative_models import GenerativeModel
from google.generativeai.types.generation_types import GenerationConfigDict
import logging

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

# Configure Gemini API key
configure(api_key=settings.GEMINI_API_KEY)

_MODEL_CACHE = {}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("gemini-router")

def get_model(model_name: Optional[str] = None):
    name = model_name or settings.DEFAULT_MODEL
    if name not in _MODEL_CACHE:
        _MODEL_CACHE[name] = GenerativeModel(name)
    return _MODEL_CACHE[name]

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if not settings.API_KEY:
        # If no API key is set in config, allow all (for dev)
        return
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")

def to_serializable_dict(obj):
    if obj is None:
        return None
    if isinstance(obj, dict):
        return {k: to_serializable_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_serializable_dict(v) for v in obj]
    if hasattr(obj, "__dict__"):
        return {k: to_serializable_dict(v) for k, v in vars(obj).items() if not k.startswith('_')}
    if hasattr(obj, "__slots__"):
        return {k: to_serializable_dict(getattr(obj, k)) for k in obj.__slots__}
    if isinstance(obj, (str, int, float, bool)):
        return obj
    return str(obj)

@app.get("/v1/health")
def health():
    logger.debug("Health check endpoint called")
    try:
        model = get_model()
        logger.debug(f"Health check using model: {model.model_name}")
        response = model.generate_content("Hello")
        if response.text:
            logger.info("Health check passed")
            return {"status": "ok"}
        else:
            logger.warning("Health check failed: No response from model.")
            return JSONResponse(status_code=503, content={"status": "error", "detail": "No response from model."})
    except Exception as e:
        logger.exception(f"Health check failed: {e}")
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(e)})

@app.post("/v1/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest, api_key: Any = Depends(verify_api_key)):
    logger.debug(f"/v1/generate called with model={req.model}, temperature={req.temperature}, max_tokens={req.max_tokens}")
    try:
        model = get_model(req.model)
        gen_config: GenerationConfigDict = {
            "temperature": req.temperature if req.temperature is not None else settings.DEFAULT_TEMPERATURE,
        }
        if req.max_tokens:
            gen_config["max_output_tokens"] = req.max_tokens
        if req.extra:
            for k in ["candidate_count", "stop_sequences", "response_mime_type", "response_schema", "presence_penalty", "frequency_penalty"]:
                if k in req.extra:
                    gen_config[k] = req.extra[k]
        logger.debug(f"Generating content with model={model.model_name}, config={gen_config}")
        response = await asyncio.to_thread(
            model.generate_content,
            req.prompt,
            generation_config=gen_config
        )
        content = response.text if hasattr(response, "text") else str(response)
        usage_obj = getattr(response, "usage_metadata", None)
        usage = to_serializable_dict(usage_obj)
        if usage is not None and not isinstance(usage, dict):
            usage = {"value": usage}
        metadata = {"model": model.model_name, "provider": "gemini"}
        logger.info("Generation successful")
        return GenerateResponse(content=content, usage=usage, metadata=metadata)
    except Exception as e:
        logger.exception(f"Error in /v1/generate: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini error: {e}")

@app.post("/v1/structured", response_model=StructuredResponse)
async def structured(req: StructuredRequest, api_key: Any = Depends(verify_api_key)):
    logger.debug(f"/v1/structured called with model={req.model}, temperature={req.temperature}, max_tokens={req.max_tokens}, schema={req.schema}")
    try:
        model = get_model(req.model)
        gen_config: GenerationConfigDict = {
            "temperature": req.temperature if req.temperature is not None else settings.DEFAULT_TEMPERATURE,
        }
        if req.max_tokens:
            gen_config["max_output_tokens"] = req.max_tokens
        if req.extra:
            for k in ["candidate_count", "stop_sequences", "response_mime_type", "response_schema", "presence_penalty", "frequency_penalty"]:
                if k in req.extra:
                    gen_config[k] = req.extra[k]
        if req.schema:
            gen_config["response_mime_type"] = "application/json"
            gen_config["response_schema"] = req.schema
        logger.debug(f"Generating structured content with model={model.model_name}, config={gen_config}")
        response = await asyncio.to_thread(
            model.generate_content,
            req.prompt,
            generation_config=gen_config
        )
        content = response.text if hasattr(response, "text") else str(response)
        import json
        try:
            result = json.loads(content)
            logger.info("Structured response parsed as JSON")
        except Exception:
            result = {"raw": content}
            logger.warning("Structured response could not be parsed as JSON")
        usage_obj = getattr(response, "usage_metadata", None)
        usage = to_serializable_dict(usage_obj)
        if usage is not None and not isinstance(usage, dict):
            usage = {"value": usage}
        metadata = {"model": model.model_name, "provider": "gemini"}
        logger.info("Structured generation successful")
        return StructuredResponse(result=result, usage=usage, metadata=metadata)
    except Exception as e:
        logger.exception(f"Error in /v1/structured: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini error: {e}") 