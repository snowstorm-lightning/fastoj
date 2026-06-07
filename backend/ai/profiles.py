import asyncio
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from backend.ai.config import PLACEHOLDER_API_KEY, AIConfig
from backend.ai.providers.base import AIProviderUnavailableError

AI_PROFILE_TTL_SECONDS = 60
AI_PROFILE_HEALTH_TIMEOUT_SECONDS = 2.0
PROFILE_IDS = ("default", "deepseek-pro", "deepseek", "qwen-local")
ADMIN_ONLY_PROFILE_IDS = {"deepseek-pro"}


@dataclass(frozen=True)
class AIProfileDefinition:
    value: str
    label_zh: str
    label_en: str
    detail_zh: str
    detail_en: str


@dataclass(frozen=True)
class AIProfileStatus:
    value: str
    configured: bool
    available: bool
    reason: str | None
    checked_at: str


@dataclass(frozen=True)
class AIProfileView:
    value: str
    label_zh: str
    label_en: str
    detail_zh: str
    detail_en: str
    configured: bool
    available: bool
    reason: str | None
    checked_at: str | None


_DEFINITIONS = {
    "default": AIProfileDefinition(
        value="default",
        label_zh="自动选择",
        label_en="Auto route",
        detail_zh="使用服务器当前可用的 AI 配置",
        detail_en="Use the currently available server AI profile",
    ),
    "deepseek": AIProfileDefinition(
        value="deepseek",
        label_zh="DeepSeek 云端",
        label_en="DeepSeek Cloud",
        detail_zh="调用 DeepSeek 兼容接口",
        detail_en="Use the DeepSeek-compatible API",
    ),
    "deepseek-pro": AIProfileDefinition(
        value="deepseek-pro",
        label_zh="DeepSeek Pro",
        label_en="DeepSeek Pro",
        detail_zh="调用 DeepSeek Pro 长上下文/强模型配置，适合管理员出题和导入题目",
        detail_en="Use the DeepSeek Pro long-context strong-model profile for admin authoring and imports",
    ),
    "qwen-local": AIProfileDefinition(
        value="qwen-local",
        label_zh="Qwen 本地",
        label_en="Local Qwen",
        detail_zh="连接本机兼容 OpenAI 接口的服务",
        detail_en="Use a local OpenAI-compatible Qwen server",
    ),
}

_cache: dict[str, tuple[AIProfileStatus, float]] = {}
_lock = threading.Lock()


def resolve_ai_config(model_profile: str | None) -> AIConfig:
    profile = (model_profile or "default").strip().lower()
    if profile != "default":
        return AIConfig.from_settings(profile)

    refresh_ai_profiles(force=False)
    for candidate in PROFILE_IDS:
        if candidate in ADMIN_ONLY_PROFILE_IDS:
            continue
        status = _cached_status(candidate)
        if status and status.available:
            return AIConfig.from_settings(candidate)
    raise AIProviderUnavailableError("AI provider is unavailable. Configure at least one usable AI profile.")


def list_ai_profiles(include_unavailable: bool, include_admin_only: bool = False) -> list[AIProfileView]:
    statuses = refresh_ai_profiles(force=False)
    views: list[AIProfileView] = []
    default_status = _default_route_status(statuses, include_admin_only=include_admin_only)
    for profile_id in PROFILE_IDS:
        if profile_id in ADMIN_ONLY_PROFILE_IDS and not include_admin_only:
            continue
        definition = _DEFINITIONS[profile_id]
        status = default_status if profile_id == "default" else statuses.get(profile_id)
        if status is None:
            status = _unchecked_status(profile_id, "AI profile has not been checked yet.")
        if include_unavailable or status.available:
            views.append(
                AIProfileView(
                    value=definition.value,
                    label_zh=definition.label_zh,
                    label_en=definition.label_en,
                    detail_zh=definition.detail_zh,
                    detail_en=definition.detail_en,
                    configured=status.configured,
                    available=status.available,
                    reason=status.reason,
                    checked_at=status.checked_at,
                )
            )
    return views


def mark_ai_profile_unavailable(profile: str | None, reason: str) -> None:
    profile_id = (profile or "default").strip().lower()
    if profile_id not in PROFILE_IDS:
        return
    safe_reason = _safe_reason(reason)
    previous = _cached_status(profile_id)
    status = AIProfileStatus(
        value=profile_id,
        configured=previous.configured if previous else True,
        available=False,
        reason=safe_reason,
        checked_at=_now_iso(),
    )
    with _lock:
        _cache[profile_id] = (status, time.monotonic())


async def refresh_ai_profiles_async(force: bool = False) -> dict[str, AIProfileStatus]:
    return await asyncio.to_thread(refresh_ai_profiles, force)


def refresh_ai_profiles(force: bool = False) -> dict[str, AIProfileStatus]:
    result: dict[str, AIProfileStatus] = {}
    for profile_id in PROFILE_IDS:
        result[profile_id] = _status_for_profile(profile_id, force)
    return result


def _status_for_profile(profile_id: str, force: bool) -> AIProfileStatus:
    cached = _cached_status(profile_id)
    if cached and not force and not _is_stale(profile_id):
        return cached
    status = _check_profile(profile_id)
    with _lock:
        _cache[profile_id] = (status, time.monotonic())
    return status


def _cached_status(profile_id: str) -> AIProfileStatus | None:
    with _lock:
        entry = _cache.get(profile_id)
    return entry[0] if entry else None


def _is_stale(profile_id: str) -> bool:
    with _lock:
        entry = _cache.get(profile_id)
    if not entry:
        return True
    return time.monotonic() - entry[1] >= AI_PROFILE_TTL_SECONDS


def _check_profile(profile_id: str) -> AIProfileStatus:
    config = AIConfig.from_settings(profile_id)
    configured, reason = _configuration_status(config)
    if not configured:
        return AIProfileStatus(profile_id, False, False, reason, _now_iso())
    available, reason = _remote_status(config)
    return AIProfileStatus(profile_id, True, available, None if available else reason, _now_iso())


def _configuration_status(config: AIConfig) -> tuple[bool, str | None]:
    if config.provider != "openai_compatible":
        if config.provider == "disabled":
            return False, "AI provider is disabled."
        return False, "Configured AI provider is not supported."
    if not config.base_url.strip():
        return False, "AI base URL is not configured."
    if not config.model.strip():
        return False, "AI model is not configured."
    if _requires_real_api_key(config) and not _has_real_api_key(config):
        return False, "DeepSeek API key is not configured."
    return True, None


def _remote_status(config: AIConfig) -> tuple[bool, str | None]:
    try:
        models_response = httpx.get(
            f"{config.base_url}/models",
            headers=_headers(config),
            timeout=AI_PROFILE_HEALTH_TIMEOUT_SECONDS,
        )
        if models_response.status_code == 200:
            models = _model_ids(models_response.json())
            if models:
                return (True, None) if config.model in models else (False, "Configured model is not available.")
        elif models_response.status_code not in {404, 405, 501}:
            return False, f"AI provider returned HTTP {models_response.status_code}."
    except httpx.RequestError:
        return False, "AI provider is unreachable."
    except (TypeError, ValueError):
        pass
    return _chat_completion_probe(config)


def _chat_completion_probe(config: AIConfig) -> tuple[bool, str | None]:
    try:
        response = httpx.post(
            f"{config.base_url}/chat/completions",
            headers=_headers(config),
            json={
                "model": config.model,
                "messages": [
                    {"role": "system", "content": "Return a tiny JSON object."},
                    {"role": "user", "content": 'Return {"ok": true}.'},
                ],
                "temperature": 0,
                "max_tokens": 8,
                "response_format": {"type": "json_object"},
            },
            timeout=AI_PROFILE_HEALTH_TIMEOUT_SECONDS,
        )
        if response.status_code == 200:
            return True, None
        return False, f"AI provider returned HTTP {response.status_code}."
    except httpx.RequestError:
        return False, "AI provider is unreachable."


def _headers(config: AIConfig) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }


def _model_ids(data: object) -> set[str]:
    items: object
    if isinstance(data, dict):
        items = data.get("data", [])
    else:
        items = data
    if not isinstance(items, list):
        return set()
    ids: set[str] = set()
    for item in items:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            ids.add(item["id"])
        elif isinstance(item, str):
            ids.add(item)
    return ids


def _default_route_status(statuses: dict[str, AIProfileStatus], include_admin_only: bool) -> AIProfileStatus:
    route_statuses = [
        status for profile_id, status in statuses.items()
        if include_admin_only or profile_id not in ADMIN_ONLY_PROFILE_IDS
    ]
    checked_values = [status.checked_at for status in route_statuses if status.checked_at]
    checked_at = max(checked_values) if checked_values else None
    configured = any(status.configured for status in route_statuses)
    available = any(status.available for status in route_statuses)
    reason = None if available else _first_reason(route_statuses) or "No available AI profile."
    return AIProfileStatus("default", configured, available, reason, checked_at or _now_iso())


def _first_reason(statuses: object) -> str | None:
    for status in statuses:
        if isinstance(status, AIProfileStatus) and status.reason:
            return status.reason
    return None


def _unchecked_status(profile_id: str, reason: str) -> AIProfileStatus:
    return AIProfileStatus(profile_id, False, False, reason, _now_iso())


def _requires_real_api_key(config: AIConfig) -> bool:
    return "api.deepseek.com" in config.base_url.lower()


def _has_real_api_key(config: AIConfig) -> bool:
    key = config.api_key.strip()
    return bool(key) and key != PLACEHOLDER_API_KEY


def _safe_reason(reason: str) -> str:
    if "unreachable" in reason.lower():
        return "AI provider is unreachable."
    if "disabled" in reason.lower():
        return "AI provider is disabled."
    if "http " in reason.lower():
        return reason.split(" for model ", 1)[0].rstrip(".") + "."
    if "deepseek profile is not configured" in reason.lower():
        return "DeepSeek API key is not configured."
    return reason[:160]


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()
