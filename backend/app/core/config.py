from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    CLERK_SECRET_KEY: str
    CLERK_PUBLISHABLE_KEY: str
    CLERK_JWKS_URL: str = "https://powerful-yak-2.clerk.accounts.dev/.well-known/jwks.json"
    ENCRYPTION_KEY: str = "generate-a-fernet-key-here"
    GROQ_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    AI_MEMORY_DEFAULT_MAX_MESSAGES: int = 200
    AGENT_BUILDER_CONTEXT_MESSAGES: int = 60

    # Comma-separated list of origins allowed to call the API from a browser
    CORS_ORIGINS: str = "http://localhost:3000"
    # Log every SQL statement the app runs (noisy; development only)
    DB_ECHO: bool = False
    # SQLite DB nodes may only open files inside this directory
    SQLITE_BASE_DIR: str = "data"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
