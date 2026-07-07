import json
import re
from typing import Any

from ai_chat_service.app.core.exception import AppException


def extract_json_object(text: str) -> dict[str, Any]:
    if not text or not text.strip():
        raise AppException(
            message="模型返回为空",
            status_code=500,
            code="empty_text",
        )
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        cleaned = json.loads(cleaned)
    except json.decoder.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 and end == -1 or end <= start:
        raise AppException(
            message="cannot find json object",
            code="JSON_NOT_FOUND",
            status_code=500,
        )
    json_text = cleaned[start: end + 1]
    try:
        parsed = json.loads(json_text)
    except json.decoder.JSONDecodeError as e:
        raise AppException(
            message="模型返回不是合法 JSON",
            code="INVALID_JSON_OUTPUT",
            status_code=500,
        ) from e

    if not isinstance(parsed, dict):
        raise AppException(
            message="模型返回 JSON 不是对象类型",
            code="INVALID_JSON_TYPE",
            status_code=500,
        )
    return parsed