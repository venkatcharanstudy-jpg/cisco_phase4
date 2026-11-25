import logging
import time
from typing import Any

import httpx

from app.exceptions import ServiceUnavailableError
from app.integrations.llm_base import LLMReply, ToolCall, ToolSpec, Turn

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS = {429, 500, 503}
# Accepted by Gemini in place of a thought signature for function calls that have none.
_SKIP_SIGNATURE = "skip_thought_signature_validator"
_SCHEMA_TYPES = {"string": "STRING", "integer": "INTEGER", "number": "NUMBER", "boolean": "BOOLEAN",
                 "object": "OBJECT", "array": "ARRAY"}


def _to_gemini_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Gemini expects upper-case type names and does not accept JSON-Schema-only keys."""
    out: dict[str, Any] = {}
    for key, value in schema.items():
        if key == "type":
            out["type"] = _SCHEMA_TYPES[value]
        elif key == "properties":
            out["properties"] = {name: _to_gemini_schema(sub) for name, sub in value.items()}
        elif key == "items":
            out["items"] = _to_gemini_schema(value)
        elif key in {"description", "enum", "required"}:
            out[key] = value
    return out


def _to_contents(turns: list[Turn]) -> list[dict[str, Any]]:
    """Map neutral turns to Gemini contents. Parallel calls from one reply must share one model turn,
    and their results one user turn, so consecutive call and result turns are merged."""
    contents: list[dict[str, Any]] = []
    open_kind: str | None = None
    for turn in turns:
        if turn.role == "model" and turn.tool_call is not None:
            part: dict[str, Any] = {"functionCall": {"name": turn.tool_call.name, "args": turn.tool_call.args}}
            if turn.tool_call.signature:
                part["thoughtSignature"] = turn.tool_call.signature
            else:
                part["thoughtSignature"] = _SKIP_SIGNATURE
            if open_kind == "calls":
                contents[-1]["parts"].append(part)
            else:
                contents.append({"role": "model", "parts": [part]})
                open_kind = "calls"
        elif turn.role == "tool":
            name = turn.tool_call.name if turn.tool_call else "tool"
            part = {"functionResponse": {"name": name, "response": {"response": turn.tool_result or {}}}}
            if open_kind == "results":
                contents[-1]["parts"].append(part)
            else:
                contents.append({"role": "user", "parts": [part]})
                open_kind = "results"
        else:
            open_kind = None
            if turn.role == "user":
                contents.append({"role": "user", "parts": [{"text": turn.text or ""}]})
            else:
                contents.append({"role": "model", "parts": [{"text": turn.text or ""}]})
    return contents


class GeminiClient:
    """Adapter from the Gemini REST generateContent API to the neutral LLMClient interface."""

    def __init__(self, api_key: str, model: str, base_url: str, timeout: float, http: httpx.Client | None = None) -> None:
        if not api_key:
            raise ServiceUnavailableError("GEMINI_API_KEY is not configured", code="llm_not_configured")
        self._api_key = api_key
        self._model = model
        self._url = f"{base_url.rstrip('/')}/models/{model}:generateContent"
        self._http = http or httpx.Client(timeout=timeout)

    def generate(self, system: str, turns: list[Turn], tools: list[ToolSpec]) -> LLMReply:
        body: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": _to_contents(turns),
        }
        if tools:
            body["tools"] = [{"functionDeclarations": [
                {"name": t.name, "description": t.description, "parameters": _to_gemini_schema(t.parameters)}
                for t in tools
            ]}]
        data = self._post(body)
        return self._parse(data)

    def _post(self, body: dict[str, Any]) -> dict[str, Any]:
        headers = {"x-goog-api-key": self._api_key, "Content-Type": "application/json"}
        reason = "no response"
        for attempt in range(3):
            try:
                resp = self._http.post(self._url, json=body, headers=headers)
            except httpx.HTTPError as exc:
                logger.warning("Gemini request failed: %s", type(exc).__name__)
                reason = f"request error ({type(exc).__name__})"
            else:
                if resp.status_code == 200:
                    return resp.json()
                reason = f"HTTP {resp.status_code}"
                logger.warning("Gemini returned HTTP %s: %s", resp.status_code, resp.text[:500])
                if resp.status_code not in _RETRYABLE_STATUS:
                    break
            time.sleep(0.5 * (attempt + 1))
        raise ServiceUnavailableError(
            f"The AI assistant is unavailable right now ({reason})",
            code="llm_unavailable",
        )

    @staticmethod
    def _parse(data: dict[str, Any]) -> LLMReply:
        candidates = data.get("candidates") or []
        if not candidates:
            raise ServiceUnavailableError("The AI assistant returned an empty response", code="llm_empty")
        parts = (candidates[0].get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts if "text" in p)
        calls = [
            ToolCall(
                name=p["functionCall"]["name"],
                args=p["functionCall"].get("args") or {},
                signature=p.get("thoughtSignature"),
            )
            for p in parts
            if "functionCall" in p
        ]
        return LLMReply(text=text, tool_calls=calls)
