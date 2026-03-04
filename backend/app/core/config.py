from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    CLERK_SECRET_KEY: str
    CLERK_PUBLISHABLE_KEY: str
    ENCRYPTION_KEY: str = "generate-a-fernet-key-here"
    GROQ_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    AI_MEMORY_DEFAULT_MAX_MESSAGES: int = 200
    AGENT_BUILDER_CONTEXT_MESSAGES: int = 60

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
