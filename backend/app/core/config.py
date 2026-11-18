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
    PLAYWRIGHT_HEADLESS: bool = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() in ("true", "1", "yes")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    BASE_DIR: Path = BASE_DIR
    _profile_dir_env = os.getenv("BROWSER_PROFILE_DIR", "browser_profile")
    BROWSER_PROFILE_DIR: Path = (
        (BASE_DIR / _profile_dir_env).resolve()
        if not Path(_profile_dir_env).is_absolute()
        else Path(_profile_dir_env).resolve()
    )
    DATA_DIR: Path = (BASE_DIR / "data").resolve()
    GEMINI_NOTEBOOK_URL: str = os.getenv(
        "GEMINI_NOTEBOOK_URL", 
        "https://gemini.google.com/notebook/455d7360-aa4b-4d50-bf2c-2bb489a5a3fd"
    )
    PROMPT_TEMPLATE_PATH: Path = (
        BASE_DIR / "Prompt Template.txt"
        if (BASE_DIR / "Prompt Template.txt").exists()
        else BASE_DIR / "Promtp Template.txt"
    )

settings = Settings()
