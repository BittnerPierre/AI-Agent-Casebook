import os
import json

import pytest

from transcript_generator.tools.research_team import ResearchTeam


class FakeRetriever:
    async def get_related_content(self, key_topics, limit=5):
        # Return a single fake content item for testing
        return [{"module_id": "mod1", "content_preview": "alpha beta gamma delta epsilon zeta"}]


def test_research_topic_writes_file(tmp_path):
    # Prepare a temporary output directory
    out_dir = tmp_path / "research_notes"
    retriever = FakeRetriever()
    team = ResearchTeam(output_dir=str(out_dir), retriever=retriever)
    section = {"section_id": "sec1", "key_topics": ["topic"]}

    notes = team.research_topic(section)
    # Validate returned structure
    assert notes["section_id"] == "sec1"
    assert isinstance(notes["knowledge_references"], list)
    ref = notes["knowledge_references"][0]
    assert ref["content_id"] == "mod1"
    assert isinstance(ref["key_points"], list) and ref["key_points"]
    assert "research_summary" in notes and isinstance(notes["research_summary"], str)

    # Validate file output matches the returned notes
    file_path = out_dir / "sec1.json"
    assert file_path.exists(), f"Expected research notes file at {file_path}"
    loaded = json.loads(file_path.read_text(encoding="utf-8"))
    assert loaded == notes