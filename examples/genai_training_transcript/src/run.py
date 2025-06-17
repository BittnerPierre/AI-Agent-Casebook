"""
Entry point for the GenAI Training Transcript Generator (Local v1).
"""
import sys
import os
import argparse

import yaml
import asyncio

# Ensure src directory is on PYTHONPATH for imports
sys.path.insert(0, os.path.dirname(__file__))

from transcript_generator.tools.knowledge_retriever import KnowledgeRetriever
from transcript_generator.tools.syllabus_loader import load_syllabus
from transcript_generator.tools.file_client_loader import load_transcripts
from transcript_generator.tools.planner import refine_syllabus
from transcript_generator.tools.research_team import aggregate_research
from transcript_generator.tools.editing_team import edit_chapters
from transcript_generator.tools.transcript_generator import generate_transcript
from transcript_generator.tools.reviewer import review_transcript

# Import Knowledge Bridge MCP interface
from knowledge_bridge.mcp_interface import create_knowledge_mcp_server


async def main(config_path: str):
    # Load configuration
    with open(config_path) as f:
        config = yaml.safe_load(f)
    # Resolve relative paths based on config file location
    config_dir = os.path.dirname(os.path.abspath(config_path))
    def _resolve(key: str) -> None:
        val = config.get(key)
        if isinstance(val, str) and not os.path.isabs(val):
            config[key] = os.path.join(config_dir, val)
    for key in [
        "syllabus_path", "raw_transcripts_dir", "preprocessed_dir",
        "course_agenda_path", "research_notes_dir", "drafts_dir", "output_dir"
    ]:
        _resolve(key)

    # Initialize Knowledge Bridge MCP Server for US-001
    print("🔗 Initializing Knowledge Bridge MCP interface...")
    output_base_path = config.get("preprocessed_dir", "output")
    knowledge_mcp_server = create_knowledge_mcp_server(output_base_path)
    
    # Check knowledge availability
    health = knowledge_mcp_server.health_check()
    if health.get("server_status") != "healthy":
        print("⚠️  Knowledge Bridge MCP server not healthy.")
        print("Please run training_manager first to preprocess course data:")
        print("  poetry run python run_training_manager.py --course-path <course-path>")
        return
    
    accessor_health = health.get("content_accessor", {})
    available_courses = accessor_health.get("available_courses", 0)
    total_modules = accessor_health.get("total_modules", 0)
    
    if available_courses == 0:
        print("⚠️  No preprocessed training data found.")
        print("Please run training_manager first to preprocess course data:")
        print("  poetry run python run_training_manager.py --course-path <course-path>")
        return
    
    print(f"✅ Knowledge Bridge MCP ready: {available_courses} courses, {total_modules} modules")
    
    # Initialize legacy knowledge retriever for backward compatibility
    knowledge_retriever = KnowledgeRetriever()
    available_courses_legacy = await knowledge_retriever.list_available_courses()
    # Load syllabus and transcripts
    modules = load_syllabus(config["syllabus_path"])
    config["modules"] = [m["title"] if isinstance(m, dict) else m for m in modules]
    transcripts = load_transcripts(config)

    # Planning: produce course agenda
    agenda = refine_syllabus(modules, config)
    agenda_path = config["course_agenda_path"]
    os.makedirs(os.path.dirname(agenda_path), exist_ok=True)
    with open(agenda_path, "w", encoding="utf-8") as f:
        f.write("# Course Agenda\n\n")
        for m in agenda:
            if isinstance(m, dict):
                f.write(f"- {m.get('title')}\n")
            else:
                f.write(f"- {m}\n")

    # Research Team: aggregate research notes
    research_notes = aggregate_research(agenda, transcripts, config)
    notes_dir = config.get("research_notes_dir", "research_notes")
    os.makedirs(notes_dir, exist_ok=True)
    for module, note in research_notes.items():
        fname = module.replace(" ", "_") + ".md"
        with open(os.path.join(notes_dir, fname), "w", encoding="utf-8") as f:
            f.write(note)

    # Editing Team: generate drafts
    drafts = edit_chapters(research_notes, config)
    drafts_dir = config.get("drafts_dir", "drafts")
    os.makedirs(drafts_dir, exist_ok=True)
    for module, draft in drafts.items():
        fname = module.replace(" ", "_") + ".md"
        with open(os.path.join(drafts_dir, fname), "w", encoding="utf-8") as f:
            f.write(draft)

    # Course Authoring: generate final transcripts
    outputs: dict[str, str] = {}
    for module, draft in drafts.items():
        outputs[module] = generate_transcript(module, draft)

    output_dir = config.get("output_dir", "output")
    os.makedirs(output_dir, exist_ok=True)
    for module, content in outputs.items():
        fname = module.replace(" ", "_") + ".md"
        with open(os.path.join(output_dir, fname), "w", encoding="utf-8") as f:
            f.write(content)

    # Review transcripts for alignment
    print("[reviewer] Reviewing final transcripts (stub)")
    for module, content in outputs.items():
        # Find syllabus entry for this module
        syllabus_item = next(
            (m for m in modules if (m.get("title") == module if isinstance(m, dict) else m == module)),
            module
        )
        research_note = research_notes.get(module, "")
        review_transcript(module, content, syllabus_item, research_note)

    print(f"Generated and reviewed {len(outputs)} module scripts in {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run GenAI Training Transcript Generator")
    parser.add_argument("--config", default="config.yaml", help="Path to the config file")
    args = parser.parse_args()
    asyncio.run(main(args.config))