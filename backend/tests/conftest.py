"""Test setup: dummy settings so the app imports without real services."""

import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CLERK_SECRET_KEY", "test")
os.environ.setdefault("CLERK_PUBLISHABLE_KEY", "test")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.components  # noqa: E402,F401  (registers node components)
