import asyncio
import logging

from fastapi import FastAPI
from app.api.routes import router
from fastapi.middleware.cors import CORSMiddleware
from app.api.projects import router as project_router
from app.api.files import router as file_router
from app.models.models import Base
from app.db.session import engine

logger = logging.getLogger("uvicorn.error")

application = FastAPI(title="SynthTeam API")


application.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@application.on_event("startup")
async def startup():
    for attempt in range(1, 11):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully.")
            break
        except Exception as e:
            logger.warning(f"DB connection attempt {attempt}/10 failed: {e}")
            await asyncio.sleep(2)
    else:
        raise RuntimeError("Could not connect to the database after 10 attempts")

    import app.components  # noqa: F401  — triggers auto-registration
    from app.components.component_registry import list_components
    logger.info(f"Registered components: {list_components()}")

    try:
        import redis.asyncio as aioredis
        from app.core.config import settings
        application.state.redis = aioredis.from_url(
            settings.REDIS_URL, decode_responses=True
        )
        logger.info("Redis client initialized for rate limiting.")
    except Exception as exc:
        logger.warning(f"Redis not available for rate limiting: {exc}")
        application.state.redis = None

    try:
        from app.scheduler import scheduler
        scheduler.start()
        logger.info("APScheduler started.")
    except Exception as exc:
        logger.warning(f"APScheduler not available: {exc}")


@application.on_event("shutdown")
async def shutdown():
    if getattr(application.state, "redis", None):
        await application.state.redis.close()

    try:
        from app.scheduler import scheduler
        scheduler.shutdown(wait=False)
    except Exception:
        pass


application.include_router(project_router)
application.include_router(file_router)
application.include_router(router)

# uvicorn entrypoint alias: `uvicorn app.main:app`
app = application
