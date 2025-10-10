from __future__ import annotations

import asyncio
import sys
import time

from openai.types.responses import ResponseTextDeltaEvent
from rich.console import Console

from agents import Runner, custom_span, gen_trace_id, trace
from agents.mcp import MCPServer

from .agents.file_search_agent import create_file_search_agent
from .agents.file_search_planning_agent import create_file_planner_agent
from .agents.file_writer_agent import create_writer_agent
from .agents.knowledge_preparation_agent import create_knowledge_preparation_agent
from .agents.schemas import (
    FileSearchItem,
    FileSearchPlan,
    FileSearchResult,
    ReportData,
    ResearchInfo,
)
from .agents.utils import save_final_report_function
from .config import get_config
from .printer import Printer


class DeepResearchManager:
    def __init__(self):
        self.console = Console()
        self.printer = Printer(self.console)
        self._config = get_config()
        # Désactiver le tracing automatique pour cet appel
        # self._run_config = RunConfig(
        #     workflow_name="deep_research",
        #     tracing_disabled=False,
        #     trace_metadata= {
        #         "config_name": self._config.config_name
        #     })

    async def run(
        self,
        fs_server: MCPServer,
        dataprep_server: MCPServer,
        query: str,
        research_info: ResearchInfo,
    ) -> None:
        self.fs_server = fs_server
        self.dataprep_server = dataprep_server
        self.research_info = research_info

        trace_id = gen_trace_id()
        with trace(
            "Deep Research", trace_id=trace_id, metadata={"config_name": self._config.config_name}
        ):
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

            self.knowledge_preparation_agent = create_knowledge_preparation_agent(
                [self.dataprep_server]
            )
            self.file_planner_agent = create_file_planner_agent([self.fs_server])
            self.file_search_agent = create_file_search_agent(
                [self.fs_server], research_info.vector_store_id
            )
            self.writer_agent = create_writer_agent([self.fs_server], do_save_report=False)

            agenda = await self._prepare_knowledge(query)
            print("\n\n=====AGENDA=====\n\n")
            print(agenda)

            search_plan = await self._plan_file_searches(agenda)
            print("\n\n=====SEARCH PLAN=====\n\n")
            print(search_plan)
            search_results = await self._perform_file_searches(search_plan)
            report = await self._write_report(query, search_results)

            final_report = f"Report summary\n\n{report.short_summary}"
            self.printer.update_item("final_report", final_report, is_done=True)

            self.printer.end()

        print("\n\n=====SAVING REPORT=====\n\n")
        _new_report = await save_final_report_function(
            self.research_info.output_dir,
            report.research_topic,
            report.markdown_report,
            report.short_summary,
            report.follow_up_questions,
        )
        print(f"Report saved: {_new_report.file_name}")
        print("\n\n=====REPORT=====\n\n")
        print(f"Report: {report.markdown_report}")
        print("\n\n=====FOLLOW UP QUESTIONS=====\n\n")
        follow_up_questions = "\n".join(report.follow_up_questions)
        print(f"Follow up questions: {follow_up_questions}")

    async def _prepare_knowledge(self, query: str) -> str:
        self.printer.update_item("preparing", "Préparation de la connaissance...")
        result = await Runner.run(
            self.knowledge_preparation_agent,
            query,
            context=self.research_info,
        )
        self.printer.update_item(
            "preparing", "Préparation de la connaissance terminée", is_done=True
        )
        return str(result.final_output)

    async def _plan_file_searches(self, query: str) -> FileSearchPlan:
        self.printer.update_item("planning", "Planification des recherches dans les fichiers...")

        result = await Runner.run(
            self.file_planner_agent,
            f"{query}",
            context=self.research_info,
        )
        self.printer.update_item(
            "planning",
            f"Effectuera {len(result.final_output.searches)} recherches dans les fichiers",
            is_done=True,
        )
        return result.final_output_as(FileSearchPlan)

    async def _perform_file_searches(self, search_plan: FileSearchPlan) -> list[str]:
        with custom_span("Recherche dans les fichiers"):
            self.printer.update_item("searching", "Recherche dans les fichiers...")
            num_completed = 0
            tasks = [asyncio.create_task(self._file_search(item)) for item in search_plan.searches]
            results = []
            for task in asyncio.as_completed(tasks):
                result = await task
                if result is not None:
                    results.append(result)
                num_completed += 1
                self.printer.update_item(
                    "searching", f"Recherche... {num_completed}/{len(tasks)} terminées"
                )
            self.printer.mark_item_done("searching")
            return results

    async def _file_search(self, item: FileSearchItem) -> str | None:
        input_text = f"Terme de recherche: {item.query}\nRaison de la recherche: {item.reason}"

        try:
            result = await Runner.run(
                self.file_search_agent,
                input_text,
                context=self.research_info,
            )
            return str(result.final_output_as(FileSearchResult).file_name)
        except Exception:
            return None

    async def _write_report(self, query: str, search_results: list[str]) -> ReportData:
        self.printer.update_item("writing", "Thinking about report...")
        # Affichage plus lisible des fichiers de résultats de recherche
        formatted_results = (
            "\n".join(f"- {fname}" for fname in search_results) if search_results else "None"
        )
        input = (
            f"Rédige un rapport de recherche exhaustif et détaillé repondant à la demande suivante:\n\n {query}.\n\n"
            f"Utilise l'agenda produit ainsi que les contenus des fichiers attachés "
            f" pour rédiger un rapport conforme aux attentes.\n\n"
            f"Search results:\n{formatted_results}"
        )

        result = Runner.run_streamed(
            self.writer_agent,
            input,
            context=self.research_info,
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
        return result.final_output_as(ReportData)
