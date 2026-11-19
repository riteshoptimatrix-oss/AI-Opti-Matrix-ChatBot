import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")


class Settings:
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    CORS_ORIGINS: list[str] = [
        origin.strip() 
        for origin in os.getenv("CORS_ORIGINS", "*").split(",") 
        if origin.strip()
    ]
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_API_KEYS: list[str] = [
        k.strip()
        for k in (os.getenv("GEMINI_API_KEYS", "") or os.getenv("GEMINI_API_KEY", "")).split(",")
        if k.strip()
    ]
    BASE_DIR: Path = BASE_DIR
    PROMPT_TEMPLATE_PATH: Path = (
        BASE_DIR / "Prompt Template.txt"
        if (BASE_DIR / "Prompt Template.txt").exists()
        else BASE_DIR / "Promtp Template.txt"
    )
    COMPANY_CONTEXT_PATH: Path = BASE_DIR / "Company's Context.txt"


settings = Settings()
