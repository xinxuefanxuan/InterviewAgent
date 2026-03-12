from __future__ import annotations

from typing import List

from interview_agent.models import InterviewPlan, InterviewQuestion, InterviewStage
from tools.websearch import WebSearchTool


class PlanAgent:
    """Responsible for topic mining + interview planning."""

    def __init__(self, websearch: WebSearchTool) -> None:
        self.websearch = websearch

    def build_plan(self, resume_text: str, role_hint: str = "Software Engineer") -> InterviewPlan:
        role = role_hint
        candidate_level = self._infer_level(resume_text)
        key_topics = self._extract_topics(resume_text)

        # Optional: search latest trends to enrich interview prompts.
        search_context = self.websearch.search(
            f"{role} interview trends {', '.join(key_topics[:3])}",
            max_results=2,
        )

        questions = self._create_questions(key_topics, search_context)
        return InterviewPlan(
            role=role,
            candidate_level=candidate_level,
            key_topics=key_topics,
            questions=questions,
        )

    def _infer_level(self, resume_text: str) -> str:
        years = 0
        for token in resume_text.lower().split():
            if token.isdigit():
                years = max(years, int(token))
        if years >= 7:
            return "Senior"
        if years >= 3:
            return "Mid"
        return "Junior"

    def _extract_topics(self, resume_text: str) -> List[str]:
        topic_candidates = [
            "python",
            "machine learning",
            "system design",
            "databases",
            "cloud",
            "llm",
            "backend",
            "frontend",
            "testing",
        ]
        lowered = resume_text.lower()
        topics = [t for t in topic_candidates if t in lowered]
        return topics or ["python", "system design", "communication"]

    def _create_questions(self, topics: List[str], search_context: List[str]) -> List[InterviewQuestion]:
        topic_a = topics[0]
        topic_b = topics[1] if len(topics) > 1 else topics[0]

        return [
            InterviewQuestion(
                stage=InterviewStage.WARMUP,
                text="请你先做一个 1 分钟自我介绍，并突出与你申请岗位最相关的经历。",
                expected_focus="结构化表达、岗位匹配度",
            ),
            InterviewQuestion(
                stage=InterviewStage.TECHNICAL,
                text=f"你在简历中提到了 {topic_a}，请介绍一个你做过的代表性项目以及关键技术决策。",
                expected_focus="技术深度、决策能力",
            ),
            InterviewQuestion(
                stage=InterviewStage.TECHNICAL,
                text=f"如果系统在 {topic_b} 场景下出现性能瓶颈，你会如何定位与优化？",
                expected_focus="问题排查与系统化思维",
            ),
            InterviewQuestion(
                stage=InterviewStage.BEHAVIORAL,
                text="讲一个你推动跨团队合作并最终达成目标的案例。",
                expected_focus="协作与影响力",
            ),
            InterviewQuestion(
                stage=InterviewStage.WRAP_UP,
                text=f"结合行业趋势（例如：{search_context[0]}），你未来 1-2 年的能力提升计划是什么？",
                expected_focus="成长意识与职业规划",
            ),
        ]
