from __future__ import annotations

import json
import urllib.request
from typing import Any, Dict, List


class LLMClient:
    """OpenAI-compatible chat completions client (works with Kimi endpoint)."""

    def __init__(self, api_key: str, base_url: str, model: str, timeout_s: int = 60) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_s = timeout_s

    def chat_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> Dict[str, Any]:
        text = self.chat_text(system_prompt, user_prompt, temperature=temperature)
        return json.loads(text)

    def chat_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        url = f"{self.base_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": self.model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        req = urllib.request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        choices: List[Dict[str, Any]] = body.get("choices", [])
        if not choices:
            raise ValueError(f"Invalid LLM response: {body}")
        return choices[0]["message"]["content"]
