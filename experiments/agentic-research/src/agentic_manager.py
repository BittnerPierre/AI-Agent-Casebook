from __future__ import annotations

from rich.console import Console

from agents import Runner, gen_trace_id, trace
from agents.mcp import MCPServer

from .agents.agentic_research_agent import create_research_supervisor_agent
from .agents.file_search_agent import create_file_search_agent
from .agents.file_search_planning_agent import create_file_planner_agent
from .agents.file_writer_agent import ReportData, create_writer_agent
from .agents.schemas import ResearchInfo
from .config import get_config
from .printer import Printer


class AgenticResearchManager:
    def __init__(self):
        self.console = Console()
        self.printer = Printer(self.console)
        self.mcp_server = None
        self._config = get_config()
        # self._run_config = RunConfig(
        #     workflow_name="agentic_research",
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

        trace_id = gen_trace_id()
        with trace(
            "Agentic Research",
            trace_id=trace_id,
            metadata={"config_name": self._config.config_name},
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

            file_planner_agent = create_file_planner_agent([self.fs_server])
            file_search_agent = create_file_search_agent(
                [self.fs_server], research_info.vector_store_id
            )
            writer_agent = create_writer_agent([self.fs_server])

            self.research_supervisor_agent = create_research_supervisor_agent(
                [self.dataprep_server], file_planner_agent, file_search_agent, writer_agent
            )

            report = await self._agentic_research(query, research_info)

            final_report = f"Report summary\n\n{report.short_summary}"
            self.printer.update_item("final_report", final_report, is_done=True)

            self.printer.end()

        print("\n\n=====REPORT=====\n\n")
        print(f"Report: {report.markdown_report}")
        print("\n\n=====FOLLOW UP QUESTIONS=====\n\n")
        follow_up_questions = "\n".join(report.follow_up_questions)
        print(f"Follow up questions: {follow_up_questions}")

    async def _agentic_research(self, query: str, research_info: ResearchInfo) -> ReportData:
        self.printer.update_item("agentic_research", "Starting Agentic Research...")

        # Désactiver le tracing automatique pour cet appel

        result = await Runner.run(
            self.research_supervisor_agent,
            f"{query}",
            context=research_info,
            max_turns=25,
        )
        self.printer.update_item(
            "agentic_research",
            "Doing Agentic Research",
            is_done=True,
        )
        return result.final_output_as(ReportData)
