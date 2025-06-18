"""
Stub for the Research Team node to aggregate cross-course content for each module.
"""

def aggregate_research(agenda, transcripts, config):
    """
    For each module in the agenda, gather context (stub returns empty content).
    """
    print("[research_team] Aggregating research notes (stub)")
    notes: dict[str, str] = {}
    for item in agenda:
        key = item.get("title") if isinstance(item, dict) else item
        content = transcripts.get(key, "")
        if not content.strip():
            raise RuntimeError(f"[research_team] No transcript source found for module: {key}. Aborting research.")
        notes[key] = content
    return notes


import os
import json
import asyncio
from typing import Any, Dict

from .knowledge_retriever import KnowledgeRetriever


class ResearchTeam:
    """
    Multi-agent ResearchTeam for knowledge integration.

    Implements research_topic(syllabus_section) producing ResearchNotes JSON files.
    Internal workflow: Researcher → Analyst → Synthesizer.
    """
    def __init__(self,
                 output_dir: str = "research_notes",
                 retriever: KnowledgeRetriever | None = None):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.retriever = retriever or KnowledgeRetriever()

    def research_topic(self, syllabus_section: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the research workflow for a syllabus section.

        Steps:
          1. Researcher: fetch relevant content via KnowledgeRetriever
          2. Analyst: select and extract key points
          3. Synthesizer: compose an overall summary

        Args:
            syllabus_section: dict with at least 'section_id' and 'key_topics'.

        Returns:
            research_notes dict matching ResearchNotes schema.
        """
        section_id = syllabus_section.get("section_id")
        key_topics = syllabus_section.get("key_topics", [])

        # 1. Researcher: fetch raw content
        raw_items = asyncio.run(self.retriever.get_related_content(key_topics))

        # 2. Analyst: extract key points for each content item
        knowledge_references: list[Dict[str, Any]] = []
        for item in raw_items:
            content_id = item.get("module_id") or item.get("content_id")
            preview = item.get("content_preview", "") or ""
            words = preview.split()
            # chunk into groups of up to 5 words
            key_points = [" ".join(words[i : i + 5]) for i in range(0, min(len(words), 15), 5)]
            knowledge_references.append({"content_id": content_id, "key_points": key_points})

        # 3. Synthesizer: build summary from key points
        summary_parts = [kp for ref in knowledge_references for kp in ref["key_points"]]
        research_summary = " ".join(summary_parts)

        notes: Dict[str, Any] = {
            "section_id": section_id,
            "knowledge_references": knowledge_references,
            "research_summary": research_summary,
        }

        # write to JSON file for MCP consumption
        out_path = os.path.join(self.output_dir, f"{section_id}.json")
        with open(out_path, "w", encoding="utf-8") as fp:
            json.dump(notes, fp, indent=2)
        return notes