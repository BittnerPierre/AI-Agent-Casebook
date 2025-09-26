import asyncio
import tempfile
import os
import time
import argparse

from src.agents.schemas import ReportData, ResearchInfo
from src.agents.file_writer_agent import create_writer_agent
from agents import Agent, Runner, RunConfig, TResponseInputItem, gen_trace_id, trace
from agents.mcp import MCPServerStdio,  MCPServer
from rich.console import Console
from src.printer import Printer
from langsmith.wrappers import OpenAIAgentsTracingProcessor
from agents import add_trace_processor
from src.config import get_config
from src.agents.utils import context_aware_filter, generate_final_report_filename, load_prompt_from_file
from .eval_utils import validate_trajectory_spec, format_trajectory_report, test_trajectory_from_existing_files, save_result_input_list_to_json, save_trajectory_evaluation_report
from src.tracing.trace_processor import FileTraceProcessor
import pprint
import json
import pprint
import re
from typing import List, Dict, Any
import sys
from .schemas import EvaluationResult
from .prompts import llm_as_judge_prompt_V2



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

# ✅ ORDRE CORRIGÉ : read_multiple_files PUIS save_report PUIS generations
TRAJECTORY_SPEC = {
    "trajectory_spec": [
        {
            "id": "load_data",
            "type": "function_call", 
            "name": "read_multiple_files",
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
            "id": "report_generation_report", 
            "type": "generation", 
            "match_regex": r"## Report",
            "expected_content": "## Report",
            "required": True
        },
        {
            "id": "save_report",
            "type": "function_call",
            "name": "save_report",
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
        self.research_info = research_info

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

            self.writer_agent = create_writer_agent([self.fs_server])

            report, messages = await self._write_report(AGENDA, SEARCH_RESULTS)

            final_report = f"Report summary\n\n{report.short_summary}"

            self.printer.update_item("final_report", final_report, is_done=True)
            self.printer.update_item("final_report_file", report.file_name, is_done=True)

            evaluation_report, evaluation_report_file = await self._evaluate_report_trajectory(report, messages)

            self.printer.update_item("evaluation_report", evaluation_report, is_done=True)
            self.printer.update_item("evaluation_report_file", evaluation_report_file, is_done=True)

            evaluation_result = await self._evaluate_report_quality(report)

            self.printer.update_item("evaluation_result", str(evaluation_result), is_done=True)

            print(f"Evaluation result: {evaluation_result.model_dump_json(indent=2)}")

            self.printer.end()


    async def _write_report(self, query: str, search_results: list[str]) -> tuple[ReportData, list[TResponseInputItem]]:
        self.printer.update_item("writing", "Thinking about report...")
        input = (  
                    "Utilise l'agenda suivant ainsi que les contenus des fichiers attachés pour rédiger un rapport de recherche exhaustif et détaillé"
                    " sur le thème \"Agent Engineer Fondations Course\" avec focus sur les systèmes multi-agents en IA."
                    f"\n\nAgenda: ß\n- "+ "\n- ".join(query) + "\n"
                    f"\n\nSearch results: \n- "+ "\n- ".join(search_results) + "\n"
                )
        
        # Désactiver le tracing automatique pour cet appel
        run_config = RunConfig(tracing_disabled=False,
                               workflow_name="write_agent_eval",
                               trace_metadata={"run_type": "evaluation"})
        
        result = Runner.run_streamed(
            self.writer_agent,
            input,
            run_config=run_config,
            context=self.research_info
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

        report = result.final_output_as(ReportData)

        messages = result.to_input_list()
        
        return report, messages

    async def _evaluate_report_trajectory(self, report: ReportData, messages: list[TResponseInputItem]) -> tuple[str, str]:

        ## EVALUATION SPECIFIC
        model_name = self.writer_agent.model
        report_file_name = report.file_name if report.file_name else generate_final_report_filename(research_topic=report.research_topic)

        # Générer le nom de base du fichier
        base_file_name = os.path.basename(report_file_name).rsplit('.md', 1)[0]
        safe_model_name = model_name.replace('/', '-')
        
        # Vérifier si le fichier original existe
        original_file_path = os.path.join(output_report_dir, report_file_name)
        if not os.path.exists(original_file_path):
            # Le fichier n'existe pas, le créer
            print(f"📝 Création du fichier rapport: {report_file_name}")
            with open(original_file_path, 'w', encoding='utf-8') as f:
                f.write(report.markdown_report)
        
        # Renommer le fichier avec le nom de modèle
        final_file_name = f"{base_file_name}_{safe_model_name}.md"
        final_file_path = os.path.join(output_report_dir, final_file_name)
        os.rename(original_file_path, final_file_path)
        print(f" Fichier renommé: {report_file_name} -> {final_file_name}")
        
        # Utiliser le nom de base pour les autres fichiers
        original_report_file_name = f"{base_file_name}.md"
        
        save_result_input_list_to_json(model_name=model_name, report_file_name=original_report_file_name, messages=messages, output_report_dir=output_report_dir)

        validation_report = validate_trajectory_spec(messages, spec)
        
        # Afficher le rapport lisible
        human_readable_report = format_trajectory_report(model_name=model_name, evaluation=validation_report, title="Writer Agent Trajectory")

        # Utilisation de la fonction pour sauvegarder le rapport
        evaluation_report_file = save_trajectory_evaluation_report(model_name=model_name, output_report_dir=output_report_dir, report_file_name=original_report_file_name, human_readable_report=human_readable_report)

        return human_readable_report, evaluation_report_file

    async def _evaluate_report_quality(self, report: ReportData) -> EvaluationResult:
        self.printer.update_item("evaluating", "Evaluating report quality...")

        report_quality_agent = Agent(
            name="report_quality_agent",
            instructions=llm_as_judge_prompt_V2,
            model="openai/gpt-4.1-mini",
            output_type=EvaluationResult,   
        )

        result = await Runner.run(
            report_quality_agent,
            report.markdown_report,
        )

        evaluation_result = result.final_output_as(EvaluationResult)

        return evaluation_result


async def main(writer_model: str = None) -> None:
    """
    Fonction principale pour l'évaluation de l'agent writer.
    
    Args:
        writer_model: Modèle à utiliser pour l'agent writer. Si None, utilise la valeur par défaut du config.
    """
    # add_trace_processor(OpenAIAgentsTracingProcessor())
    add_trace_processor(FileTraceProcessor(log_dir="traces"))

    config = get_config()
    # anthropic models does not seems to work (issue with json output)
    # "litellm/anthropic/claude-3-7-sonnet-latest"
    #"litellm/anthropic/claude-3-5-haiku-latest"
    # Mistral is working very WELL
    # Mistral small is working very WELL
    # OpenAI models
    # "openai/gpt-4.1-mini" # does not call the function save_report
    # "openai/gpt-4.1" does not call the function save_report
    if writer_model:
        config.models.writer_model = writer_model

    print(f"Writer model: {config.models.writer_model}")

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

        add_trace_processor(OpenAIAgentsTracingProcessor())

        research_info = ResearchInfo(
            temp_dir=canonical_tmp_dir,
            output_dir=output_report_dir)
        
        evaluation_manager = EvaluationManager()
        await evaluation_manager.run(fs_server, research_info)

def eval_main():
    """
    Point d'entrée synchrone pour les scripts Poetry.
    Parse les arguments CLI et passe le modèle à main().
    """
    parser = argparse.ArgumentParser(description="Évaluation de l'agent writer")
    parser.add_argument(
        "--writer-model", 
        type=str, 
        help="Modèle à utiliser pour l'agent writer. "
             "Valeurs recommandées: openai/gpt-5-mini, litellm/mistral/mistral-medium-latest, openai/gpt-4.1"
    )
    
    # Parse seulement les arguments connus pour éviter les erreurs avec d'autres arguments
    args, unknown = parser.parse_known_args()
    
    asyncio.run(main(writer_model=args.writer_model))

def test_main():
    """
    🚀 Point d'entrée pour tester la trajectoire et la qualité du rapport sur des fichiers existants
    Usage: poetry run test_trajectory <file_prefix>
    
    Args:
        file_prefix: Préfixe du fichier (ex: "evaluations/output/agent_engineer_fondations_course_final_report_20250715_161950")
                    Le script cherchera automatiquement les fichiers _messages.json et _final_report.md correspondants
    """
    if len(sys.argv) != 2:
        print("Usage: poetry run test_trajectory <file_prefix>")
        print("\nExemple:")
        print("poetry run test_trajectory evaluations/output/agent_engineer_fondations_course_final_report_20250715_161950")
        print("\nLe script cherchera automatiquement:")
        print("- <file_prefix>_messages.json (pour la trajectoire)")
        print("- <file_prefix>_final_report.md (pour la qualité du rapport)")
        return
    
    file_prefix = sys.argv[1]
    messages_file = f"{file_prefix}_messages.json"
    report_file = f"{file_prefix}.md"
    
    print(f"🔍 Test de trajectoire et qualité sur: {file_prefix}")
    print("=" * 80)
    
    # Vérifier que les fichiers existent
    if not os.path.exists(messages_file):
        print(f"❌ Fichier messages non trouvé: {messages_file}")
        return
    
    if not os.path.exists(report_file):
        print(f"❌ Fichier rapport non trouvé: {report_file}")
        return
    
    print(f"✅ Fichier messages trouvé: {messages_file}")
    print(f"✅ Fichier rapport trouvé: {report_file}")
    print()
    
    # 1. Test de la trajectoire
    print("📊 1. Test de la trajectoire...")
    print("-" * 40)
    spec = TRAJECTORY_SPEC["trajectory_spec"]
    trajectory_report = test_trajectory_from_existing_files(messages_file, spec)
    print(trajectory_report)
    
    # Sauvegarder le rapport de trajectoire
    trajectory_report_file = f"{file_prefix}_trajectory_test.txt"
    with open(trajectory_report_file, 'w', encoding='utf-8') as f:
        f.write(trajectory_report)
    print(f"\n💾 Rapport de trajectoire sauvegardé: {trajectory_report_file}")
    
    # 2. Test de la qualité du rapport
    print("\n📈 2. Test de la qualité du rapport...")
    print("-" * 40)
    
    try:
        # Lire le contenu du rapport
        with open(report_file, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        # Créer un objet ReportData minimal pour l'évaluation
        report_data = ReportData(
            research_topic="Agent Engineer Fondations Course",
            report=report_content,
            file_name=os.path.basename(report_file),
            short_summary="Rapport de test chargé depuis fichier",
            follow_up_questions=[]
        )
        
        # Évaluer la qualité du rapport
        async def evaluate_quality():
            return await EvaluationManager()._evaluate_report_quality(report_data)
        
        # Exécuter l'évaluation de qualité
        evaluation_result = asyncio.run(evaluate_quality())
        
        print("📊 Résultat de l'évaluation de qualité:")
        print(f"{evaluation_result.model_dump_json(indent=2)}")
        
        # Sauvegarder le résultat de l'évaluation de qualité
        quality_report_file = f"{file_prefix}_quality_evaluation.json"
        with open(quality_report_file, 'w', encoding='utf-8') as f:
            f.write(evaluation_result.model_dump_json(indent=2))
        print(f"\n💾 Résultat de qualité sauvegardé: {quality_report_file}")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'évaluation de la qualité: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Tests terminés!")

if __name__ == "__main__":
    eval_main()