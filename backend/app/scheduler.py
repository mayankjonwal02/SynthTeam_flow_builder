"""
APScheduler integration for cron-triggered workflows.

Provides a module-level AsyncIOScheduler and helpers to
add/remove cron jobs keyed by workflow ID.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger("uvicorn.error")

scheduler = AsyncIOScheduler()


def add_cron_job(job_id: str, cron_expr: str, callback, **kwargs):
    """
    Register a cron-triggered job.

    Args:
        job_id:    Unique identifier (e.g. "cron_{workflow_id}").
        cron_expr: Standard 5-field crontab expression.
        callback:  Async callable to invoke on each trigger.
        **kwargs:  Extra keyword arguments forwarded to the callback.
    """
    trigger = CronTrigger.from_crontab(cron_expr)
    scheduler.add_job(
        callback,
        trigger,
        id=job_id,
        replace_existing=True,
        kwargs=kwargs,
    )
    logger.info(f"Cron job registered: {job_id} [{cron_expr}]")


def remove_cron_job(job_id: str):
    """Remove a cron job by ID (no-op if it does not exist)."""
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Cron job removed: {job_id}")
