from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone


class SecurityError(ValueError):
    """Raised when token or cryptographic validation fails."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(24)


def generate_api_key(prefix: str = "cpk_live") -> str:
    """Generate a random API key in `prefix_random` format."""
    return f"{prefix}_{secrets.token_urlsafe(24)}"


def api_key_prefix(api_key: str, prefix_length: int = 16) -> str:
    return api_key[:prefix_length]


def api_key_salt() -> str:
    return secrets.token_hex(16)


def hash_api_key(api_key: str, *, salt: str, pepper: str) -> str:
    digest = hashlib.sha256(f"{salt}:{api_key}:{pepper}".encode("utf-8")).hexdigest()
    return digest


def verify_api_key_hash(api_key: str, *, salt: str, pepper: str, expected_hash: str) -> bool:
    computed = hash_api_key(api_key, salt=salt, pepper=pepper)
    return hmac.compare_digest(computed, expected_hash)


def hash_refresh_token(refresh_token: str, *, secret: str) -> str:
    return hashlib.sha256(f"{secret}:{refresh_token}".encode("utf-8")).hexdigest()


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def issue_jwt_token(
    *,
    payload: dict,
    secret: str,
    ttl_seconds: int,
) -> str:
    """Issue an HS256 JWT token with iat/exp claims."""
    now = int(utc_now().timestamp())
    claims = dict(payload)
    claims["iat"] = now
    claims["exp"] = now + ttl_seconds

    header = {"alg": "HS256", "typ": "JWT"}
    header_part = _b64url_encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    payload_part = _b64url_encode(json.dumps(claims, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signing_input = f"{header_part}.{payload_part}".encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_part = _b64url_encode(signature)
    return f"{header_part}.{payload_part}.{signature_part}"


def decode_jwt_token(token: str, *, secret: str, leeway_seconds: int = 0) -> dict:
    """Decode and validate an HS256 JWT token."""
    try:
        header_part, payload_part, signature_part = token.split(".")
    except ValueError as exc:
        raise SecurityError("Invalid JWT format") from exc

    signing_input = f"{header_part}.{payload_part}".encode("ascii")
    expected_sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    received_sig = _b64url_decode(signature_part)
    if not hmac.compare_digest(expected_sig, received_sig):
        raise SecurityError("Invalid JWT signature")

    try:
        payload = json.loads(_b64url_decode(payload_part).decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise SecurityError("Invalid JWT payload") from exc

    exp = payload.get("exp")
    if not isinstance(exp, int):
        raise SecurityError("Missing JWT expiration")
    now = int(utc_now().timestamp())
    if exp + leeway_seconds < now:
        raise SecurityError("JWT expired")
    return payload


def compute_expiry(ttl_seconds: int) -> datetime:
    return utc_now() + timedelta(seconds=ttl_seconds)
