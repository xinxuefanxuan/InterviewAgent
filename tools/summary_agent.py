from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import List, Optional

from interview_agent.models import Turn
from llm.client import LLMClient


@dataclass
class InterviewReport:
    overall_score: float
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]


class SummaryAgent:
    """Analyzes interview turns and generates scoring + feedback."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.llm_client = llm_client
        self.system_prompt = Path("prompts/summary_prompt.txt").read_text(encoding="utf-8")

    def summarize(self, turns: List[Turn]) -> InterviewReport:
        if not turns:
            return InterviewReport(
                overall_score=0.0,
                strengths=["尚未完成作答，无法评估优势。"],
                weaknesses=["缺少有效回答内容。"],
                suggestions=["先进行一次完整模拟，再生成报告。"],
            )

        if self.llm_client:
            try:
                return self._summarize_with_llm(turns)
            except Exception:
                pass

        overall = round(mean(t.score for t in turns), 2)

        strengths = [
            "表达结构较完整" if any(len(t.answer) > 80 for t in turns) else "回答简洁直接",
            "能覆盖问题核心要点" if overall >= 7 else "有一定问题理解能力",
        ]
        weaknesses = [
            "技术细节深度不足" if overall < 7 else "部分案例可增加量化结果",
            "高压追问下的应对策略可加强",
        ]
        suggestions = [
            "使用 STAR 模型组织行为题回答（情境-任务-行动-结果）。",
            "技术题补充：背景约束、方案对比、指标提升、复盘反思。",
            "每次回答控制在 1-2 分钟，先结论后展开。",
        ]

        return InterviewReport(
            overall_score=overall,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
        )

    def _summarize_with_llm(self, turns: List[Turn]) -> InterviewReport:
        transcript = []
        for i, turn in enumerate(turns, start=1):
            transcript.append(
                f"Q{i}: {turn.question}\nA{i}: {turn.answer}\nHeuristicScore: {turn.score}\n"
            )
        user_prompt = "\n".join(transcript)

        result = self.llm_client.chat_json(self.system_prompt, user_prompt, temperature=0.2)
        return InterviewReport(
            overall_score=float(result.get("overall_score", 0)),
            strengths=result.get("strengths", []),
            weaknesses=result.get("weaknesses", []),
            suggestions=result.get("suggestions", []),
        )
