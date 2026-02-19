from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    CLERK_SECRET_KEY: str
    CLERK_PUBLISHABLE_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
