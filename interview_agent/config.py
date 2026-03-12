from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class AppConfig:
    # LLM (Kimi/OpenAI-compatible)
    llm_enabled: bool = os.getenv("LLM_ENABLED", "true").lower() == "true"
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.moonshot.cn/v1")
    llm_model: str = os.getenv("LLM_MODEL", "kimi-k2-0905-preview")
    llm_timeout_s: int = int(os.getenv("LLM_TIMEOUT_S", "60"))

    # Speech-to-text
    stt_provider: str = os.getenv("STT_PROVIDER", "whisper")  # whisper | funasr
    whisper_base_url: str = os.getenv("WHISPER_BASE_URL", "https://api.openai.com/v1")
    whisper_api_key: str = os.getenv("WHISPER_API_KEY", "")
    whisper_model: str = os.getenv("WHISPER_MODEL", "whisper-1")

    # Text-to-speech
    tts_provider: str = os.getenv("TTS_PROVIDER", "edge")  # edge | volc | tencent
    edge_voice: str = os.getenv("EDGE_TTS_VOICE", "zh-CN-XiaoxiaoNeural")

    volc_tts_endpoint: str = os.getenv("VOLC_TTS_ENDPOINT", "")
    volc_app_id: str = os.getenv("VOLC_APP_ID", "")
    volc_access_token: str = os.getenv("VOLC_ACCESS_TOKEN", "")
    volc_voice_type: str = os.getenv("VOLC_VOICE_TYPE", "zh_female_qingxin")

    tencent_secret_id: str = os.getenv("TENCENT_SECRET_ID", "")
    tencent_secret_key: str = os.getenv("TENCENT_SECRET_KEY", "")
    tencent_region: str = os.getenv("TENCENT_REGION", "ap-beijing")
    tencent_voice_type: int = int(os.getenv("TENCENT_VOICE_TYPE", "101001"))


settings = AppConfig()
