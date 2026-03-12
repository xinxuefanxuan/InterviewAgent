from __future__ import annotations

import uuid
from dataclasses import asdict
from typing import Dict

from interview_agent.models import InterviewSession
from tools.plan_agent import PlanAgent
from tools.summary_agent import SummaryAgent


class InterviewAgent:
    """Main orchestrator that coordinates PlanAgent/SummaryAgent/toolset."""

    def __init__(self, plan_agent: PlanAgent, summary_agent: SummaryAgent) -> None:
        self.plan_agent = plan_agent
        self.summary_agent = summary_agent
        self.sessions: Dict[str, InterviewSession] = {}

    def start_session(self, resume_text: str, role_hint: str) -> dict:
        plan = self.plan_agent.build_plan(resume_text=resume_text, role_hint=role_hint)
        session_id = str(uuid.uuid4())

        session = InterviewSession(
            session_id=session_id,
            resume_text=resume_text,
            plan=plan,
        )
        self.sessions[session_id] = session

        first_question = session.next_question()
        return {
            "session_id": session_id,
            "role": plan.role,
            "candidate_level": plan.candidate_level,
            "key_topics": plan.key_topics,
            "question": first_question.text if first_question else "暂无问题",
        }

    def answer_question(self, session_id: str, answer_text: str) -> dict:
        session = self._get_session(session_id)
        current_question = session.next_question()
        if not current_question:
            return {"done": True, "message": "面试已结束，请查看总结报告。"}

        notes, score = self._evaluate_answer(current_question.text, answer_text)
        session.add_turn(answer=answer_text, notes=notes, score=score)

        next_question = session.next_question()
        if next_question is None:
            return {
                "done": True,
                "message": "面试问题已完成，请调用 complete 获取总结。",
            }

        return {
            "done": False,
            "score": score,
            "notes": notes,
            "next_question": next_question.text,
        }

    def complete_session(self, session_id: str) -> dict:
        session = self._get_session(session_id)
        report = self.summary_agent.summarize(session.turns)

        return {
            "session_id": session.session_id,
            "turns": [asdict(t) for t in session.turns],
            "report": asdict(report),
        }

    def _get_session(self, session_id: str) -> InterviewSession:
        if session_id not in self.sessions:
            raise ValueError(f"Session not found: {session_id}")
        return self.sessions[session_id]

    def _evaluate_answer(self, question: str, answer: str) -> tuple[str, float]:
        length_score = min(len(answer) / 120, 1.0) * 5
        keyword_bonus = 0
        for token in ["结果", "指标", "优化", "复盘", "挑战"]:
            if token in answer:
                keyword_bonus += 1
        total = round(min(10.0, length_score + keyword_bonus), 2)

        notes = (
            f"问题: {question} | 反馈: 回答长度 {'充足' if len(answer) >= 80 else '偏短'}，"
            f"建议补充可量化结果与技术决策细节。"
        )
        return notes, total
