from __future__ import annotations

import uuid
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pypdf import PdfReader

from interview_agent.config import settings
from interview_agent.core import InterviewAgent
from llm.client import LLMClient
from services.stt import FunASRSTTService, WhisperSTTService
from services.tts import EdgeTTSService, TencentTTSService, VolcTTSService
from tools.plan_agent import PlanAgent
from tools.summary_agent import SummaryAgent
from tools.websearch import WebSearchTool

app = FastAPI(title="InterviewAgent API")
AUDIO_DIR = Path("app/static_audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


class AnswerRequest(BaseModel):
    session_id: str
    answer_text: str


class CompleteRequest(BaseModel):
    session_id: str


class TTSRequest(BaseModel):
    text: str


def create_llm_client() -> LLMClient | None:
    if not settings.llm_enabled or not settings.llm_api_key:
        return None
    return LLMClient(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        timeout_s=settings.llm_timeout_s,
    )


def create_stt_service():
    provider = settings.stt_provider.lower()
    if provider == "funasr":
        return FunASRSTTService()
    return WhisperSTTService(
        base_url=settings.whisper_base_url,
        api_key=settings.whisper_api_key,
        model=settings.whisper_model,
    )


def create_tts_service():
    provider = settings.tts_provider.lower()
    if provider == "volc":
        return VolcTTSService(
            endpoint=settings.volc_tts_endpoint,
            app_id=settings.volc_app_id,
            access_token=settings.volc_access_token,
            voice_type=settings.volc_voice_type,
        )
    if provider == "tencent":
        return TencentTTSService(
            secret_id=settings.tencent_secret_id,
            secret_key=settings.tencent_secret_key,
            region=settings.tencent_region,
            voice_type=settings.tencent_voice_type,
        )
    return EdgeTTSService(voice=settings.edge_voice)


llm_client = create_llm_client()
websearch = WebSearchTool()
plan_agent = PlanAgent(websearch=websearch, llm_client=llm_client)
summary_agent = SummaryAgent(llm_client=llm_client)
interview_agent = InterviewAgent(plan_agent=plan_agent, summary_agent=summary_agent)
stt_service = create_stt_service()
tts_service = create_tts_service()


def extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    content = []
    for page in reader.pages:
        content.append(page.extract_text() or "")
    return "\n".join(content).strip()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "llm_enabled": bool(llm_client),
        "stt_provider": settings.stt_provider,
        "tts_provider": settings.tts_provider,
    }


@app.post("/session/start")
async def start_session(
    role_hint: str = Form("Software Engineer"),
    resume_pdf: UploadFile = File(...),
) -> dict:
    data = await resume_pdf.read()
    resume_text = extract_pdf_text(data)
    if not resume_text:
        resume_text = "No text parsed from PDF."

    return interview_agent.start_session(resume_text=resume_text, role_hint=role_hint)


@app.post("/session/answer")
def answer_session(req: AnswerRequest) -> dict:
    return interview_agent.answer_question(req.session_id, req.answer_text)


@app.post("/session/answer_audio")
async def answer_audio(session_id: str = Form(...), answer_audio: UploadFile = File(...)) -> dict:
    suffix = Path(answer_audio.filename or "answer.wav").suffix or ".wav"
    tmp_path = AUDIO_DIR / f"in-{uuid.uuid4()}{suffix}"
    tmp_path.write_bytes(await answer_audio.read())

    try:
        text = stt_service.transcribe(tmp_path).strip()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"STT failed: {exc}") from exc
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    if not text:
        raise HTTPException(status_code=400, detail="STT produced empty transcript")

    result = interview_agent.answer_question(session_id, text)
    result["transcript"] = text
    return result


@app.post("/session/complete")
def complete_session(req: CompleteRequest) -> dict:
    return interview_agent.complete_session(req.session_id)


@app.post("/speech/tts")
async def text_to_speech(req: TTSRequest):
    output = AUDIO_DIR / f"tts-{uuid.uuid4()}.mp3"
    try:
        await tts_service.synthesize_to_file(req.text, output)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"TTS failed: {exc}") from exc
    return FileResponse(path=output, media_type="audio/mpeg", filename=output.name)
