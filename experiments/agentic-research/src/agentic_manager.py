from __future__ import annotations

import asyncio
import time

from rich.console import Console

from agents import Runner, custom_span, gen_trace_id, trace, RunConfig

# from .agents.file_planner_agent import file_planner_agent
from .agents.file_search_agent import file_search_agent
from .agents.writer_agent import ReportData, writer_agent
from .agents.schemas import FileSearchPlan, FileSearchItem
from .printer import Printer
from .agents.agentic_research_agent import research_agent

class ResearchManager:
    def __init__(self):
        self.console = Console()
        self.printer = Printer(self.console)

    async def run(self, query: str) -> None:
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
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
            report = await self._agentic_research(query)
            # report = await self._write_report(query, search_results)

            final_report = f"Report summary\n\n{report.short_summary}"
            self.printer.update_item("final_report", final_report, is_done=True)

            self.printer.end()

        print("\n\n=====REPORT=====\n\n")
        print(f"Report: {report.markdown_report}")
        print("\n\n=====FOLLOW UP QUESTIONS=====\n\n")
        follow_up_questions = "\n".join(report.follow_up_questions)
        print(f"Follow up questions: {follow_up_questions}")

    async def _agentic_research(self, query: str) -> ReportData:
        self.printer.update_item("agentic_research", "Starting Agentic Research...")
        
        # Désactiver le tracing automatique pour cet appel
        run_config = RunConfig(tracing_disabled=False)
        
        result = await Runner.run(
            research_agent,
            f"Requête: {query}",
            run_config=run_config
        )
        self.printer.update_item(
            "agentic_research",
            f"Doing Agentic Research",
            is_done=True,
        )
        return result.final_output_as(FileSearchPlan)

    # async def _perform_file_searches(self, search_plan: FileSearchPlan) -> list[str]:
    #     with custom_span("Recherche dans les fichiers"):
    #         self.printer.update_item("searching", "Recherche dans les fichiers...")
    #         num_completed = 0
    #         tasks = [asyncio.create_task(self._file_search(item)) for item in search_plan.searches]
    #         results = []
    #         for task in asyncio.as_completed(tasks):
    #             result = await task
    #             if result is not None:
    #                 results.append(result)
    #             num_completed += 1
    #             self.printer.update_item(
    #                 "searching", f"Recherche... {num_completed}/{len(tasks)} terminées"
    #             )
    #         self.printer.mark_item_done("searching")
    #         return results

    # async def _file_search(self, item: FileSearchItem) -> str | None:
    #     input_text = f"Terme de recherche: {item.query}\nRaison de la recherche: {item.reason}"
    #     try:
    #         # Désactiver le tracing automatique pour cet appel
    #         run_config = RunConfig(tracing_disabled=False)
            
    #         result = await Runner.run(
    #             file_search_agent,
    #             input_text,
    #             run_config=run_config
    #         )
    #         return str(result.final_output)
    #     except Exception:
    #         return None

    # async def _write_report(self, query: str, search_results: list[str]) -> ReportData:
    #     self.printer.update_item("writing", "Thinking about report...")
    #     input = f"Original query: {query}\nSummarized search results: {search_results}"
        
    #     # Désactiver le tracing automatique pour cet appel
    #     run_config = RunConfig(tracing_disabled=False)
        
    #     result = Runner.run_streamed(
    #         writer_agent,
    #         input,
    #         run_config=run_config
    #     )
    #     update_messages = [
    #         "Thinking about report...",
    #         "Planning report structure...",
    #         "Writing outline...",
    #         "Creating sections...",
    #         "Cleaning up formatting...",
    #         "Finalizing report...",
    #         "Finishing report...",
    #     ]

    #     last_update = time.time()
    #     next_message = 0
    #     async for _ in result.stream_events():
    #         if time.time() - last_update > 5 and next_message < len(update_messages):
    #             self.printer.update_item("writing", update_messages[next_message])
    #             next_message += 1
    #             last_update = time.time()

    #     self.printer.mark_item_done("writing")
    #     return result.final_output_as(ReportData)
