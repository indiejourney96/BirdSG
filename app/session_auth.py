from __future__ import annotations

import base64
import hmac
import json
import os
import time
from hashlib import sha256
from pathlib import Path
from typing import Any

from fastapi import Request

AUTH_SESSION_HEADER = "x-birdsg-session"
AUTH_COOKIE_NAME = "birdsg_session"

try:
    from dotenv import load_dotenv

    load_dotenv()

    frontend_env = Path(__file__).resolve().parents[1] / "frontend" / ".env.local"
    if frontend_env.exists():
        load_dotenv(frontend_env)
except ImportError:
    pass


def _b64url_decode(value: str) -> bytes:
    normalized = value.replace("-", "+").replace("_", "/")
    padded = normalized + "=" * (-len(normalized) % 4)
    return base64.b64decode(padded)


def _get_session_secret() -> str:
    secret = os.environ.get("AUTH_SESSION_SECRET", "").strip()
    if not secret:
        raise RuntimeError("Missing AUTH_SESSION_SECRET.")
    return secret


def verify_session_token(token: str) -> dict[str, Any] | None:
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
    except ValueError:
        return None

    try:
        secret = _get_session_secret().encode("utf-8")
        expected_signature = hmac.new(
            secret,
            f"{header_segment}.{payload_segment}".encode("utf-8"),
            sha256,
        ).digest()
        provided_signature = _b64url_decode(signature_segment)

        if not hmac.compare_digest(expected_signature, provided_signature):
            return None

        payload = json.loads(_b64url_decode(payload_segment).decode("utf-8"))
        exp = payload.get("exp")

        if not payload.get("sub") or not payload.get("email") or not exp:
            return None

        if int(exp) <= int(time.time()):
            return None

        return payload
    except Exception:
        return None


def get_authenticated_user_id(request: Request) -> str | None:
    token = request.headers.get(AUTH_SESSION_HEADER)

    if not token:
        token = request.cookies.get(AUTH_COOKIE_NAME)

    if not token:
        return None

    session = verify_session_token(token)
    return session.get("sub") if session else None
