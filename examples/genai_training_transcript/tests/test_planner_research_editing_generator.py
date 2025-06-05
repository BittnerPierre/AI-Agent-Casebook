from src.tools.planner import refine_syllabus
from src.tools.research_team import aggregate_research
from src.tools.editing_team import edit_chapters
from src.tools.transcript_generator import generate_transcript

def test_refine_syllabus():
    modules = ["A", "B"]
    result = refine_syllabus(modules, {})
    assert result == modules

def test_aggregate_research():
    agenda = ["X"]
    transcripts = {"X": "content"}
    result = aggregate_research(agenda, transcripts, {})
    assert isinstance(result, dict) and "X" in result

def test_edit_chapters():
    notes = {"M": "notes"}
    result = edit_chapters(notes, {})
    assert isinstance(result, dict) and result["M"] == "notes"

def test_generate_transcript():
    output = generate_transcript("M", "draft", {})
    assert isinstance(output, str) and "M" in output