from __future__ import annotations

import mimetypes
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class BaseSTTService(ABC):
    @abstractmethod
    def transcribe(self, audio_path: Path) -> str:
        raise NotImplementedError


class WhisperSTTService(BaseSTTService):
    """Whisper via OpenAI-compatible audio transcription API."""

    def __init__(self, base_url: str, api_key: str, model: str = "whisper-1") -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def transcribe(self, audio_path: Path) -> str:
        import requests

        content_type = mimetypes.guess_type(audio_path.name)[0] or "application/octet-stream"
        with audio_path.open("rb") as f:
            files = {"file": (audio_path.name, f, content_type)}
            data = {"model": self.model}
            headers = {"Authorization": f"Bearer {self.api_key}"}
            url = f"{self.base_url}/audio/transcriptions"
            resp = requests.post(url, headers=headers, files=files, data=data, timeout=120)
            resp.raise_for_status()
            body = resp.json()
            return body.get("text", "").strip()


class FunASRSTTService(BaseSTTService):
    """FunASR local inference (requires funasr installed)."""

    def __init__(self, model: str = "paraformer-zh") -> None:
        self.model = model
        self._model: Optional[object] = None
        self.instance_id = str(uuid.uuid4())

    def _ensure_model(self) -> None:
        if self._model is not None:
            return
        from funasr import AutoModel  # lazy import

        self._model = AutoModel(model=self.model)

    def transcribe(self, audio_path: Path) -> str:
        self._ensure_model()
        result = self._model.generate(input=str(audio_path))
        if isinstance(result, list) and result:
            return str(result[0].get("text", "")).strip()
        if isinstance(result, dict):
            return str(result.get("text", "")).strip()
        return str(result).strip()
