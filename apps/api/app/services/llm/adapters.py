from __future__ import annotations

import os
from typing import Any

import httpx

from app.config import settings


async def call_ollama(
    base_url: str, model: str, system: str, user: str
) -> str:
    url = base_url.rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "")


async def call_openai_compat(
    base_url: str,
    model: str,
    system: str,
    user: str,
    api_key_env: str | None,
) -> str:
    key = os.environ.get(api_key_env or "", "")
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
    }
    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def call_anthropic(
    base_url: str,
    model: str,
    system: str,
    user: str,
    api_key_env: str | None,
) -> str:
    key = os.environ.get(api_key_env or "", "")
    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    url = base_url.rstrip("/") + "/v1/messages"
    payload: dict[str, Any] = {
        "model": model,
        "max_tokens": 4096,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        parts = data.get("content", [])
        return "".join(p.get("text", "") for p in parts if p.get("type") == "text")


async def ping_provider(name: str, base_url: str | None) -> tuple[bool, str]:
    if not base_url:
        return False, "missing base_url"
    try:
        async with httpx.AsyncClient(timeout=min(10.0, settings.http_timeout_seconds)) as client:
            if name == "ollama":
                resp = await client.get(base_url.rstrip("/") + "/api/tags")
            elif name == "anthropic":
                # Lightweight reachability; may 401 without key — still means host up
                resp = await client.get(base_url.rstrip("/"))
            else:
                resp = await client.get(base_url.rstrip("/"))
            if resp.status_code < 500:
                return True, f"http {resp.status_code}"
            return False, f"http {resp.status_code}"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
