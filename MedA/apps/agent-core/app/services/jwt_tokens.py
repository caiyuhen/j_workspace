"""JWT issuing/verification for MedA bearer tokens.

The token carries the session identity and an expiry so an attacker cannot mint
one without the signing key, and a leaked token stops working on its own. The
matching `AuthSession` row is still the source of truth for revocation, so
verification here is a first gate, not the whole check.
"""

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt

ALGORITHM = "HS256"
DEV_FALLBACK_SECRET = "meda-dev-insecure-secret-do-not-use-in-production"
DEFAULT_TTL_SECONDS = 12 * 60 * 60


class TokenError(Exception):
    """Raised when a bearer token is malformed, unsigned by us, or expired."""


def get_secret() -> str:
    return os.getenv("MEDA_JWT_SECRET") or DEV_FALLBACK_SECRET


def get_ttl_seconds() -> int:
    raw = os.getenv("MEDA_JWT_TTL_SECONDS")
    if not raw:
        return DEFAULT_TTL_SECONDS
    try:
        ttl = int(raw)
    except ValueError as exc:
        raise TokenError(f"MEDA_JWT_TTL_SECONDS is not an integer: {raw!r}") from exc
    if ttl <= 0:
        raise TokenError(f"MEDA_JWT_TTL_SECONDS must be positive: {ttl}")
    return ttl


def issue_token(
    *,
    user_id: str,
    organization_slug: str,
    role: str,
    client_type: str,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "org": organization_slug,
        "role": role,
        "client_type": client_type,
        "jti": uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=get_ttl_seconds())).timestamp()),
    }
    return jwt.encode(payload, get_secret(), algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            get_secret(),
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub", "jti"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError(f"invalid token: {exc}") from exc
