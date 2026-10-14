import asyncio
import logging

from fastapi import FastAPI
from app.api.routes import router
from fastapi.middleware.cors import CORSMiddleware
from app.api.projects import router as project_router
from app.api.files import router as file_router
from app.api.db_connections import router as db_connections_router
from app.models.models import Base
from app.db.session import engine
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

application = FastAPI(title="SynthTeam API")


application.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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

    import app.db_connectors  # noqa: F401  — triggers connector registration
    from app.db_connectors.connector_registry import list_connectors
    logger.info(f"Registered DB connectors: {list_connectors()}")

    try:
        import app.ai  # noqa: F401  — triggers AI provider/tool registration
        from app.ai.llm.registry import list_llm_providers
        from app.ai.tools.registry import list_tools
        logger.info(f"Registered LLM providers: {list_llm_providers()}")
        logger.info(f"Registered AI tools: {list_tools()}")
    except Exception as exc:
        logger.warning(f"AI layer not fully available (install langchain deps): {exc}")

    from app.utils.encryption import encryption_key_is_valid
    if not encryption_key_is_valid():
        logger.warning(
            "ENCRYPTION_KEY is not a valid Fernet key: saving DB connections will fail. "
            "See docs/configuration.md."
        )

    try:
        import redis.asyncio as aioredis
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

    # Deployed routes live in memory: re-register them (and their cron jobs)
    try:
        from app.runtime.deployment import restore_deployed_routes
        await restore_deployed_routes(application)
    except Exception as exc:
        logger.error(f"Could not restore deployed routes: {exc}")


@application.on_event("shutdown")
async def shutdown():
    if getattr(application.state, "redis", None):
        await application.state.redis.close()

    try:
        from app.scheduler import scheduler
        scheduler.shutdown(wait=False)
    except Exception:
        pass

    try:
        from app.db_connectors.pool_manager import shutdown_all_pools
        await shutdown_all_pools()
    except Exception:
        pass


application.include_router(project_router)
application.include_router(file_router)
application.include_router(db_connections_router)
application.include_router(router)

try:
    from app.ai.a2a.router import router as a2a_router
    application.include_router(a2a_router)
except ImportError:
    pass

try:
    from app.multi_agent.api import router as agent_builder_router
    from app.multi_agent.ws import router as agent_ws_router
    application.include_router(agent_builder_router)
    application.include_router(agent_ws_router)
except ImportError as exc:
    logger.warning(f"Multi-agent builder not available: {exc}")

# uvicorn entrypoint alias: `uvicorn app.main:app`
app = application
