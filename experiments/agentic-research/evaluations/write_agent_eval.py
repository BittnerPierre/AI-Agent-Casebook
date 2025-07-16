import asyncio
import tempfile
import os
import time

from src.agents.schemas import ReportData, ResearchInfo
from src.agents.writer_agent import create_writer_agent
from agents import Runner, RunConfig, gen_trace_id, set_trace_processors, trace
from agents.mcp import MCPServerStdio,  MCPServer
from rich.console import Console
from src.printer import Printer
from langsmith.wrappers import OpenAIAgentsTracingProcessor
from agents import add_trace_processor
from src.config import get_config
from src.agents.utils import context_aware_filter, generate_final_report_filename
from .eval_utils import validate_trajectory_spec, format_trajectory_report, test_trajectory_from_existing_files, save_result_input_list_to_json, save_trajectory_evaluation_report
from src.tracing.trace_processor import FileTraceProcessor
import pprint
import json
import pprint
import re
from typing import List, Dict, Any
import sys


# Files used as knowledge base to generate the report
# it is the result of file_search_agent
# it is generated with a RAG pipeline using the vector store on which we have loaded the raw transcript
# files are in temp_dir
SEARCH_RESULTS = [
     "architecture_fondamentale_des_systemes_multi_agents_ai.txt",
    #  "mecanismes_avances_de_planification_coordination_et_orchestration_dans_les_systemes_multi_agents_intelligents.txt",
    #  "gestion_de_la_memoire_dans_les_systemes_multi_agents_ai.txt",
    #  "outils_et_frameworks_de_developpement_pour_systemes_multi_agents_ai.txt",
    #  "mecanismes_de_collaboration_inter_agents.txt",
    #  "etudes_de_cas_reels_de_systemes_multi_agents_ai.txt",
    #  "defis_techniques_et_limitations_des_systemes_multi_agents_ai.txt",
    #  "methodologies_de_prototypage_et_developpement_d_assistants_ai_multi_outils_approches_iteratives_tests_validation_et_amelioration_continue.txt",
    #  "perspectives_theoriques_et_prospectives_des_systemes_multi_agents_modeles_computationnels_intelligence_collective_emergence_et_implications_philosophiques.txt"
]

# Agenda of the report as should be proposed by the lead researcher agent
AGENDA = [
    "Fondamentaux des agents intelligents et leurs architectures",
    # "Concepts avancés de planification multi-agent et orchestration",
    # "Workflow de gestion de la mémoire (courte et longue durée) dans les agents",
    # "Utilisation pratique des outils dans les agents AI",
    # "Collaboration et coordination entre plusieurs agents",
    # "Exemples concrets et études de cas comme le système multi-agent d'Anthropic",
    # "Défis techniques et solutions pour la mise en œuvre",
    # "Méthodes de prototypage et développement d'assistants AI multi-outils",
    # "Aspects théoriques et pratiques du système"
]

# ✅ ORDRE CORRIGÉ : read_multiple_files PUIS save_final_report PUIS generations
TRAJECTORY_SPEC = {
    "trajectory_spec": [
        {
            "id": "load_data",
            "type": "function_call", 
            "name": "read_multiple_files",
            "required": True
        },
        {
            "id": "save_report",
            "type": "function_call",
            "name": "save_final_report",
            "required": True
        },
        {
            "id": "report_generation_raw_notes",
            "type": "generation",
            "match_regex": r"## Raw Notes",
            "expected_content": "## Raw Notes",
            "required": True
        },
        {
            "id": "report_generation_detailed_agenda",
            "type": "generation",
            "match_regex": r"## Detailed Agenda",
            "expected_content": "## Detailed Agenda",
            "required": True
        },
        {
            "id": "report_generation_final_report", 
            "type": "generation", 
            "match_regex": r"## Final Report",
            "expected_content": "## Final Report",
            "required": True
        }
    ]
}

spec = TRAJECTORY_SPEC["trajectory_spec"]

# répertoire où charger les notes intermédiaires de recherche
temp_search_dir = "evaluations/temp_search_dir"
# répertoire où enregistrer le rapport final
output_report_dir = "evaluations/output_report_dir"


class EvaluationManager:

    def __init__(self):
        self.console = Console()
        self.printer = Printer(self.console)


    async def run(self, fs_server: MCPServer, research_info: ResearchInfo) -> None:
        self.fs_server = fs_server
        trace_id = gen_trace_id()
        with trace("Writer Agent Evaluation trace", trace_id=trace_id, metadata={"trace_type": "evaluation"}):
            self.printer.update_item(
                "trace_id",
                f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}",
                is_done=True,
                hide_checkmark=True,
            )

            self.printer.update_item(
                "starting",
                "Démarrage de la recherche dans les fichiers...",
                is_done=True,
                hide_checkmark=True,
            )

            report = await self._write_report(fs_server, AGENDA, SEARCH_RESULTS, research_info)

            final_report = f"Report summary\n\n{report.short_summary}"
            self.printer.update_item("final_report", final_report, is_done=True)
            self.printer.update_item("final_report_file", report.file_name, is_done=True)

            self.printer.end()


    async def _write_report(self, fs_server: MCPServer, agenda: str, search_results: list[str], research_info: ResearchInfo) -> ReportData:
        self.printer.update_item("writing", "Thinking about report...")
        input = (  
                    "Utilise l'agenda suivant ainsi que les contenus des fichiers attachés pour rédiger un rapport de recherche exhaustif et détaillé"
                    " sur le thème \"Agent Engineer Fondations Course\" avec focus sur les systèmes multi-agents en IA."
                    f"\n\nAgenda: \n- "+ "\n- ".join(agenda) + "\n"
                    f"\n\nSearch results: \n- "+ "\n- ".join(search_results) + "\n"
                )
        
        # Désactiver le tracing automatique pour cet appel
        run_config = RunConfig(tracing_disabled=False,
                               workflow_name="write_agent_eval",
                               trace_metadata={"run_type": "evaluation"})

        writer_agent = create_writer_agent([self.fs_server])
        
        result = Runner.run_streamed(
            writer_agent,
            input,
            run_config=run_config,
            context=research_info
        )
        update_messages = [
            "Thinking about report...",
            "Planning report structure...",
            "Writing outline...",
            "Creating sections...",
            "Cleaning up formatting...",
            "Finalizing report...",
            "Finishing report...",
        ]

        last_update = time.time()
        next_message = 0
        async for _ in result.stream_events():
            if time.time() - last_update > 5 and next_message < len(update_messages):
                self.printer.update_item("writing", update_messages[next_message])
                next_message += 1
                last_update = time.time()

        self.printer.mark_item_done("writing")

        messages = result.to_input_list()
        report = result.final_output_as(ReportData)

        report_file_name = report.file_name if report.file_name else generate_final_report_filename(research_topic=report.research_topic)

        save_result_input_list_to_json(model_name=writer_agent.model, report_file_name=report_file_name, messages=messages, output_report_dir=output_report_dir)

        validation_report = validate_trajectory_spec(messages, spec)
        
        # Afficher le rapport lisible
        human_readable_report = format_trajectory_report(model_name=writer_agent.model, evaluation=validation_report, title="Writer Agent Trajectory")
        print("\n" + human_readable_report)
        

        # Utilisation de la fonction pour sauvegarder le rapport
        save_trajectory_evaluation_report(output_report_dir, report_file_name, human_readable_report)
        
        return report


async def main() -> None:
    # add_trace_processor(OpenAIAgentsTracingProcessor())
    add_trace_processor(FileTraceProcessor(log_dir="traces"))

    config = get_config()
    # anthropic models does not seems to work (issue with json output)
    # "litellm/anthropic/claude-3-7-sonnet-latest"
    #"litellm/anthropic/claude-3-5-haiku-latest"
    # Mistral is working very WELL
    # "litellm/mistral/mistral-medium-latest" 
    # OpenAI models
    # "openai/gpt-4.1-mini" # does not call the function save_final_report
    # "openai/gpt-4.1" does not call the function save_final_report
    config.models.writer_model = "openai/gpt-4.1"

    canonical_tmp_dir = os.path.realpath(temp_search_dir)
    print(f"Canonical tmp dir: {canonical_tmp_dir}")
    if not os.path.exists(canonical_tmp_dir):
        print("temp_dir does not exist, exiting")
        return

    fs_server = MCPServerStdio(
        name="FS_MCP_SERVER",
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", temp_search_dir],
        },
        tool_filter=context_aware_filter,
        cache_tools_list=True
    )
    async with fs_server:

        research_info = ResearchInfo(
            temp_dir=canonical_tmp_dir,
            output_dir=output_report_dir)
        
        evaluation_manager = EvaluationManager()
        await evaluation_manager.run(fs_server, research_info)

def eval_main():
    """Sync entrypoint for Poetry scripts."""
    asyncio.run(main())

def test_main():
    """
    🚀 Point d'entrée pour tester la trajectoire sur des fichiers existants
    Usage: poetry run test_trajectory <messages_file.json>
    """
    if len(sys.argv) != 2:
        print("Usage: poetry run test_trajectory <messages_file.json>")
        print("\nExemple:")
        print("poetry run test_trajectory evaluations/output/agent_engineer_fondations_course_final_report_20250715_161950_messages.json")
        return
    
    messages_file = sys.argv[1]
    
    print(f"🔍 Test de trajectoire sur: {messages_file}")
    print("=" * 60)
    
    # Tester avec le spec actuel
    spec = TRAJECTORY_SPEC["trajectory_spec"]
    report = test_trajectory_from_existing_files(messages_file, spec)
    print(report)
    
    # Sauvegarder le rapport
    report_file = messages_file.replace('_messages.json', '_trajectory_test.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n💾 Rapport sauvegardé: {report_file}")

if __name__ == "__main__":
    eval_main()