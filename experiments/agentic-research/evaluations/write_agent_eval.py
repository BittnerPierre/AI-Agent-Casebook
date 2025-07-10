import asyncio
import tempfile
import os
import time

from src.agents.schemas import ReportData, ResearchInfo
from src.agents.writer_agent import create_writer_agent
from agents import Runner, RunConfig, gen_trace_id, trace
from agents.mcp import MCPServerStdio,  MCPServer
from rich.console import Console
from src.printer import Printer
from langsmith.wrappers import OpenAIAgentsTracingProcessor
from agents.tracing import add_trace_processor
from src.config import get_config
from src.agents.utils import context_aware_filter

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

temp_dir = "evaluations/temp_dir"
output_dir = "evaluations/output"


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
            print(report)

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

        print(result.to_input_list())
        
        return result.final_output_as(ReportData)


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