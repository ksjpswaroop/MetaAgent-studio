from __future__ import annotations

import json
from typing import Any


def strip_markdown(raw: str) -> str:
    """Strip markdown fences before json.loads (AGENTS.md SOP)."""
    text = raw.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def parse_json_content(raw: str) -> Any:
    return json.loads(strip_markdown(raw))
