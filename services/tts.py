from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from abc import ABC, abstractmethod
from pathlib import Path


class BaseTTSService(ABC):
    @abstractmethod
    async def synthesize_to_file(self, text: str, output_path: Path) -> Path:
        raise NotImplementedError


class EdgeTTSService(BaseTTSService):
    def __init__(self, voice: str = "zh-CN-XiaoxiaoNeural") -> None:
        self.voice = voice

    async def synthesize_to_file(self, text: str, output_path: Path) -> Path:
        import edge_tts

        communicate = edge_tts.Communicate(text=text, voice=self.voice)
        await communicate.save(str(output_path))
        return output_path


class VolcTTSService(BaseTTSService):
    """火山引擎 TTS HTTP 版本（按官方 endpoint 配置）。"""

    def __init__(self, endpoint: str, app_id: str, access_token: str, voice_type: str) -> None:
        self.endpoint = endpoint
        self.app_id = app_id
        self.access_token = access_token
        self.voice_type = voice_type

    async def synthesize_to_file(self, text: str, output_path: Path) -> Path:
        import requests

        payload = {
            "app": {"appid": self.app_id, "token": self.access_token, "cluster": "volcano_tts"},
            "user": {"uid": "interview-agent"},
            "audio": {"voice_type": self.voice_type, "encoding": "mp3"},
            "request": {"reqid": str(int(time.time() * 1000)), "text": text, "text_type": "plain"},
        }
        resp = requests.post(self.endpoint, json=payload, timeout=60)
        resp.raise_for_status()
        body = resp.json()
        audio_b64 = body.get("data")
        if not audio_b64:
            raise ValueError(f"Invalid volc tts response: {body}")
        output_path.write_bytes(base64.b64decode(audio_b64))
        return output_path


class TencentTTSService(BaseTTSService):
    """腾讯云 TTS (TC3-HMAC-SHA256 签名调用)。"""

    def __init__(self, secret_id: str, secret_key: str, region: str, voice_type: int) -> None:
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.region = region
        self.voice_type = voice_type

    async def synthesize_to_file(self, text: str, output_path: Path) -> Path:
        import requests

        service = "tts"
        host = "tts.tencentcloudapi.com"
        endpoint = f"https://{host}"
        action = "TextToVoice"
        version = "2019-08-23"
        timestamp = int(time.time())
        date = time.strftime("%Y-%m-%d", time.gmtime(timestamp))

        payload = json.dumps(
            {
                "Text": text,
                "SessionId": f"interview-{timestamp}",
                "ModelType": 1,
                "VoiceType": self.voice_type,
                "Codec": "mp3",
            }
        )

        canonical_headers = f"content-type:application/json; charset=utf-8\nhost:{host}\n"
        signed_headers = "content-type;host"
        hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        canonical_request = (
            "POST\n/\n\n"
            f"{canonical_headers}\n{signed_headers}\n{hashed_request_payload}"
        )

        algorithm = "TC3-HMAC-SHA256"
        credential_scope = f"{date}/{service}/tc3_request"
        string_to_sign = (
            f"{algorithm}\n{timestamp}\n{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )

        def _sign(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        secret_date = _sign(("TC3" + self.secret_key).encode("utf-8"), date)
        secret_service = _sign(secret_date, service)
        secret_signing = _sign(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        authorization = (
            f"{algorithm} Credential={self.secret_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )

        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json; charset=utf-8",
            "Host": host,
            "X-TC-Action": action,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Version": version,
            "X-TC-Region": self.region,
        }

        resp = requests.post(endpoint, headers=headers, data=payload, timeout=60)
        resp.raise_for_status()
        body = resp.json()
        response = body.get("Response", {})
        audio_b64 = response.get("Audio")
        if not audio_b64:
            raise ValueError(f"Invalid tencent tts response: {body}")
        output_path.write_bytes(base64.b64decode(audio_b64))
        return output_path
