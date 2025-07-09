from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class GenerateRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stop: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None

class GenerateResponse(BaseModel):
    content: str
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class StructuredRequest(BaseModel):
    prompt: str
    schema: Dict[str, Any]
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stop: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None

class StructuredResponse(BaseModel):
    result: Dict[str, Any]
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None 