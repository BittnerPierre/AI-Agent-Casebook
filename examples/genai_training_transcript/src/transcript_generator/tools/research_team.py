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


import asyncio
import json
import os
from typing import Any

from .knowledge_retriever import KnowledgeRetriever

# LangSmith tracing support
from agents import set_trace_processors
from langsmith.wrappers import OpenAIAgentsTracingProcessor


class ResearchTeam:
    """
    Multi-agent ResearchTeam for knowledge integration.

    Implements research_topic(syllabus_section) producing ResearchNotes JSON files.
    Internal workflow: Researcher → Analyst → Synthesizer.
    """
    def __init__(self,
                 output_dir: str = "research_notes",
                 retriever: KnowledgeRetriever | None = None,
                 config: dict[str, Any] | None = None):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.retriever = retriever or KnowledgeRetriever()
        cfg = config or {}
        # number of key points to extract per content item
        self.max_key_points = cfg.get("max_key_points_per_item", 3)
        # number of words per key point
        self.words_per_key_point = cfg.get("words_per_key_point", 5)
        # optional max length for summary string (in characters)
        self.max_summary_length = cfg.get("max_summary_length")
        
        # Configure LangSmith tracing for research agents
        self.langsmith_enabled = False
        langsmith_api_key = os.getenv('LANGSMITH_API_KEY')
        langsmith_project = os.getenv('LANGSMITH_PROJECT', 'story-ops')
        langsmith_tracing = os.getenv('LANGSMITH_TRACING', '').lower() == 'true'
        
        if langsmith_api_key and langsmith_tracing:
            try:
                # Configure tracing processor for OpenAI Agents SDK
                os.environ['LANGSMITH_API_KEY'] = langsmith_api_key
                os.environ['LANGSMITH_PROJECT'] = langsmith_project
                
                # Set up trace processors for agents
                set_trace_processors([OpenAIAgentsTracingProcessor()])
                
                self.langsmith_enabled = True
                print(f"[ResearchTeam] LangSmith tracing configured for project: {langsmith_project}")
            except Exception as e:
                print(f"[ResearchTeam] Failed to configure LangSmith tracing: {e}")
        else:
            if not langsmith_api_key:
                print("[ResearchTeam] LANGSMITH_API_KEY not found. LangSmith tracing disabled.")
            if not langsmith_tracing:
                print("[ResearchTeam] LANGSMITH_TRACING not enabled. LangSmith tracing disabled.")

    def research_topic(self, syllabus_section: dict[str, Any]) -> dict[str, Any]:
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

        # 1. Researcher: fetch raw content via KnowledgeRetriever (or MCP bridge)
        try:
            raw_items = asyncio.run(self.retriever.get_related_content(key_topics))
        except Exception as e:
            print(f"[ResearchTeam] error fetching content for {section_id}: {e}")
            raw_items = []

        # 2. Analyst: extract key points for each content item
        knowledge_references: list[dict[str, Any]] = []
        for item in raw_items:
            content_id = item.get("module_id") or item.get("content_id")
            preview = item.get("content_preview", "") or ""
            words = preview.split()
            # chunk into groups based on configured parameters
            max_words = self.max_key_points * self.words_per_key_point
            key_points: list[str] = []
            for start in range(0, min(len(words), max_words), self.words_per_key_point):
                chunk = words[start : start + self.words_per_key_point]
                if chunk:
                    key_points.append(" ".join(chunk))
                if len(key_points) >= self.max_key_points:
                    break
            knowledge_references.append({"content_id": content_id, "key_points": key_points})

        # 3. Synthesizer: build summary from key points
        summary_parts = [kp for ref in knowledge_references for kp in ref["key_points"]]
        research_summary = " ".join(summary_parts)
        # apply optional summary length cap
        if self.max_summary_length is not None:
            research_summary = research_summary[: self.max_summary_length]

        notes: dict[str, Any] = {
            "section_id": section_id,
            "knowledge_references": knowledge_references,
            "research_summary": research_summary,
        }

        # write to JSON file for MCP consumption
        out_path = os.path.join(self.output_dir, f"{section_id}.json")
        try:
            with open(out_path, "w", encoding="utf-8") as fp:
                json.dump(notes, fp, indent=2)
        except Exception as e:
            print(f"[ResearchTeam] error writing notes file {out_path}: {e}")
        return notes