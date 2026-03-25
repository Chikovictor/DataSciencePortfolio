import time
from hashlib import sha256

from django.core.cache import cache


def client_identifier(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _normalized_rate_part(value):
    if value is None:
        return "default"
    normalized = str(value).strip().lower()
    if not normalized:
        return "default"
    return sha256(normalized.encode("utf-8")).hexdigest()


def is_rate_limited(request, scope, limit, window_seconds, identifier_suffix=None):
    now = int(time.time())
    key = (
        f"rate-limit:{scope}:{client_identifier(request)}:"
        f"{_normalized_rate_part(identifier_suffix)}"
    )
    timestamps = cache.get(key, [])
    timestamps = [value for value in timestamps if value > now - window_seconds]

    if len(timestamps) >= limit:
        cache.set(key, timestamps, timeout=window_seconds)
        return True

    timestamps.append(now)
    cache.set(key, timestamps, timeout=window_seconds)
    return False
