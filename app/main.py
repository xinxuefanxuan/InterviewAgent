from __future__ import annotations

from io import BytesIO

from fastapi import FastAPI, File, Form, UploadFile
from pydantic import BaseModel
from pypdf import PdfReader

from interview_agent.core import InterviewAgent
from tools.plan_agent import PlanAgent
from tools.summary_agent import SummaryAgent
from tools.websearch import WebSearchTool

app = FastAPI(title="InterviewAgent API")

websearch = WebSearchTool()
plan_agent = PlanAgent(websearch=websearch)
summary_agent = SummaryAgent()
interview_agent = InterviewAgent(plan_agent=plan_agent, summary_agent=summary_agent)


class AnswerRequest(BaseModel):
    session_id: str
    answer_text: str


class CompleteRequest(BaseModel):
    session_id: str


def extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    content = []
    for page in reader.pages:
        content.append(page.extract_text() or "")
    return "\n".join(content).strip()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


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


@app.post("/session/complete")
def complete_session(req: CompleteRequest) -> dict:
    return interview_agent.complete_session(req.session_id)
