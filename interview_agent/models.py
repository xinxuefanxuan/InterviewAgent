from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class InterviewStage(str, Enum):
    WARMUP = "warmup"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    WRAP_UP = "wrap_up"
    COMPLETE = "complete"


@dataclass
class InterviewQuestion:
    stage: InterviewStage
    text: str
    expected_focus: str


@dataclass
class Turn:
    question: str
    answer: str
    notes: str
    score: float


@dataclass
class InterviewPlan:
    role: str
    candidate_level: str
    key_topics: List[str]
    questions: List[InterviewQuestion]


@dataclass
class InterviewSession:
    session_id: str
    resume_text: str
    plan: InterviewPlan
    current_question_index: int = 0
    turns: List[Turn] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return self.current_question_index >= len(self.plan.questions)

    def next_question(self) -> Optional[InterviewQuestion]:
        if self.is_complete:
            return None
        return self.plan.questions[self.current_question_index]

    def add_turn(self, answer: str, notes: str, score: float) -> None:
        question = self.next_question()
        if question is None:
            return

        self.turns.append(
            Turn(
                question=question.text,
                answer=answer,
                notes=notes,
                score=score,
            )
        )
        self.current_question_index += 1
