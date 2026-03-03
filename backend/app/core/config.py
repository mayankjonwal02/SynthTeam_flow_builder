from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    CLERK_SECRET_KEY: str
    CLERK_PUBLISHABLE_KEY: str
    ENCRYPTION_KEY: str = "generate-a-fernet-key-here"
    GROQ_API_KEY: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
