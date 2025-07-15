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
from src.agents.utils import context_aware_filter
from .eval_utils import extract_full_trajectory, extract_tool_trajectory, evaluate_tools_trajectory, validate_trajectory_spec
from src.tracing.trace_processor import FileTraceProcessor
import pprint
import json
import pprint


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

# Spécification de la trajectoire attendue
# Ce la correspond au CoT (Chain of Thought) + ReACT de l'agent writer.
TRAJECTORY_SPEC_MODEL = {
    "trajectory_spec": [
        {
            "id": "load_data",
            "type": "function_call",
            "name": "read_multiple_files",
            "required": True
        },
        {
            "id": "extract_raw_notes",
            "type": "generation",
            "match_regex": "^## Raw Notes",
            "required": True
        },
        {
            "id": "create_outline",
            "type": "generation",
            "match_regex": "^## Detailed Agenda",
            "required": True
        },
        {
            "id": "write_sections",
            "type": "generation",
            "match_regex": "^###",
            "required": True
        },
        {
            "id": "save_report",
            "type": "function_call",
            "name": "save_final_report",
            "required": True
        },
        {
            "id": "handoff_agent",
            "type": "function_call",
            "name_prefix": "transfer_to_",
            "required": False
        }
    ]
}

spec = TRAJECTORY_SPEC_MODEL["trajectory_spec"]

# répertoire où charger les notes intermédiaires de recherche
temp_dir = "evaluations/temp_dir"
# répertoire où enregistrer le rapport final
output_dir = "evaluations/output"


class EvaluationManager:

    def __init__(self):
        self.console = Console()
        self.printer = Printer(self.console)

    def _save_result_input_list_to_json(self, report_file_name: str, messages: list) -> None:
        """
        Sauvegarde la liste des messages au format JSON dans le répertoire output_dir,
        en adaptant le nom du fichier à partir du nom du rapport (remplace .txt par _messages.json).
        """
        base_file_name = os.path.basename(report_file_name).rsplit('.md', 1)[0]
        messages_file_name = f"{base_file_name}_messages.json"
        output_path = os.path.join(output_dir, messages_file_name)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)


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

        self._save_result_input_list_to_json(report.file_name, messages)


        # 1) extraire la trajectoire complète
        # full_traj = extract_full_trajectory(messages)

        # # 2) n'en garder que les tool calls
        # tool_traj = extract_tool_trajectory(full_traj)

        # # 3) comparer à la référence
        # reference = ["read_multiple_files", "save_final_report"]
        # report = evaluate_tools_trajectory(tool_traj, reference)

        
        # print(json.dumps({
        #     "full_trajectory": full_traj,
        #     "tool_trajectory": tool_traj,
        #     "evaluation": report
        # }, indent=2, ensure_ascii=False))

        validation_report = validate_trajectory_spec(messages, spec)

        pprint.pprint(validation_report)

        return report


async def main() -> None:
    add_trace_processor(OpenAIAgentsTracingProcessor())

    config = get_config()
    # anthropic models does not seems to work (issue with json output)
    # "litellm/anthropic/claude-3-7-sonnet-latest"
    #"litellm/anthropic/claude-3-5-haiku-latest"
    config.models.writer_model = "litellm/mistral/mistral-medium-latest"   # "openai/gpt-4.1-mini"

    canonical_tmp_dir = os.path.realpath(temp_dir)
    print(f"Canonical tmp dir: {canonical_tmp_dir}")
    if not os.path.exists(canonical_tmp_dir):
        print("temp_dir does not exist, exiting")
        return
    
    set_trace_processors([FileTraceProcessor(log_dir="traces")])

    fs_server = MCPServerStdio(
        name="FS_MCP_SERVER",
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", temp_dir],
        },
        tool_filter=context_aware_filter,
        cache_tools_list=True
    )
    async with fs_server:

        research_info = ResearchInfo(
            temp_dir=canonical_tmp_dir,
            output_dir=output_dir)
        
        evaluation_manager = EvaluationManager()
        await evaluation_manager.run(fs_server, research_info)





def eval_main():
    """Sync entrypoint for Poetry scripts."""
    asyncio.run(main())

if __name__ == "__main__":
    eval_main()