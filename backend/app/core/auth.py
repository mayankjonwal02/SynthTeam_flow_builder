import time
import requests
from jose import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

CLERK_JWKS_URL = settings.CLERK_JWKS_URL
security = HTTPBearer()

# Cache JWKS keys with a TTL so rotated keys are picked up automatically
_jwks_cache: dict = {}
_jwks_fetched_at: float = 0
_JWKS_TTL = 3600  # re-fetch every hour


def _get_jwks(force_refresh: bool = False) -> dict:
    global _jwks_cache, _jwks_fetched_at
    now = time.time()
    if not force_refresh and _jwks_cache and (now - _jwks_fetched_at < _JWKS_TTL):
        return _jwks_cache
    _jwks_cache = requests.get(CLERK_JWKS_URL, timeout=10).json()
    _jwks_fetched_at = now
    return _jwks_cache


def _find_key(jwks: dict, kid: str) -> dict | None:
    for k in jwks.get("keys", []):
        if k["kid"] == kid:
            return k
    return None


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials

    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        # Try cached keys first
        jwks = _get_jwks()
        key = _find_key(jwks, kid)

        # If kid not found, keys may have rotated — force refresh once
        if key is None:
            jwks = _get_jwks(force_refresh=True)
            key = _find_key(jwks, kid)

        if key is None:
            raise HTTPException(status_code=401, detail="Unknown signing key")

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={
                "verify_exp": True,
                "verify_aud": False,   # Clerk session tokens may not carry an aud claim
            },
        )

        return payload  # contains sub = user_id

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid auth token")
