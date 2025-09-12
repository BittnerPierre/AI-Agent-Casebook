from typing import List, Literal
from pydantic import BaseModel, Field

Judgment = Literal["PASS", "FAIL", "BORDERLINE"]
Grade = Literal["A", "B", "C", "D", "E"]

class Grades(BaseModel):
    format: Grade = Field(description="Format correctness: A–E")
    grounding: Grade = Field(description="Grounding in Raw Notes: A–E")
    agenda: Grade = Field(description="Agenda adherence: A–E")
    usability: Grade = Field(description="Output usability: A–E")

class EvaluationResult(BaseModel):
    judgment: Judgment = Field(description='Overall decision: "PASS" | "FAIL" | "BORDERLINE"')
    grades: Grades
    reasoning: str = Field(description="4–6 sentence summary of the evaluation")
    missing_raw_notes: List[str] = Field(default_factory=list, description="Unused key concepts from Raw Notes")
    missing_agenda_items: List[str] = Field(default_factory=list, description="Agenda items not covered or weakly covered")
    off_topic_signals: List[str] = Field(default_factory=list, description="Detected signals indicating non-research format")

    # Optionnel : applique la règle métier pour proposer un jugement
    def compute_judgment(self) -> Judgment:
        """
        Business rule:
        - PASS if majority of grades are A/B and no hard fail.
        - FAIL if 2 or more grades are D/E.
        - Otherwise BORDERLINE.
        """
        g = [self.grades.format, self.grades.grounding, self.grades.agenda, self.grades.usability]
        de_count = sum(1 for x in g if x in ("D", "E"))
        ab_count = sum(1 for x in g if x in ("A", "B"))
        if de_count >= 2:
            return "FAIL"
        if ab_count >= 3:
            return "PASS"
        return "BORDERLINE"

    def __str__(self) -> str:
        return f"EvaluationResult(judgment={self.judgment}, reasoning={self.reasoning[:50]}...)"