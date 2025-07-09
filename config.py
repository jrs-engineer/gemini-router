import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DEFAULT_MODEL: str = os.getenv("GEMINI_MODEL", "models/gemini-2.0-flash")
    DEFAULT_TEMPERATURE: float = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))
    API_KEY: str = os.getenv("ROUTER_API_KEY", "")  # Optional, for router auth

settings = Settings() 