#!/usr/bin/env python3
"""
GenAI Training Transcript Generator CLI (US-009)

End-to-end CLI integration for complete syllabus → transcript generation workflow.
Uses WorkflowOrchestrator as main pipeline for seamless component integration.

Usage:
    transcript-generator --syllabus <file> [options]

Author: Claude Code - Sprint 1 Week 4
Reference: US-009 End-to-End CLI Integration (Issue #57)
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file for OPENAI_API_KEY and other environment variables
except ImportError:
    # dotenv not available, environment variables must be set manually
    pass

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from knowledge_bridge.mcp_interface import create_knowledge_mcp_server
from transcript_generator.tools.syllabus_loader import load_syllabus
from transcript_generator.workflow_orchestrator import (
    WorkflowConfig,
    WorkflowOrchestrator,
    WorkflowResult,
)

# Add integration_tests to path for utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../integration_tests'))
from test_utils import transform_syllabus_structure


class CLIFormatter:
    """Rich console formatter for CLI output"""
    
    def __init__(self):
        self.console = Console()
    
    def print_header(self, title: str):
        """Print CLI header with title"""
        self.console.print(Panel(
            f"[bold blue]{title}[/bold blue]",
            title="🤖 GenAI Training Transcript Generator",
            border_style="blue"
        ))
    
    def print_phase(self, phase_name: str, description: str):
        """Print workflow phase information"""
        self.console.print(f"\n[bold green]📋 {phase_name}[/bold green]")
        self.console.print(f"   {description}")
    
    def print_success(self, message: str):
        """Print success message"""
        self.console.print(f"[green]✅ {message}[/green]")
    
    def print_warning(self, message: str):
        """Print warning message"""
        self.console.print(f"[yellow]⚠️  {message}[/yellow]")
    
    def print_error(self, message: str):
        """Print error message"""
        self.console.print(f"[red]❌ {message}[/red]")
    
    def print_info(self, message: str):
        """Print info message"""
        self.console.print(f"[blue]ℹ️  {message}[/blue]")
    
    def print_results_table(self, workflow_result: WorkflowResult):
        """Print formatted results table"""
        table = Table(title="📊 Workflow Execution Results")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        table.add_row("Status", "✅ Success" if workflow_result.success else "❌ Failed")
        table.add_row("Execution Time", f"{workflow_result.execution_time:.2f}s" if workflow_result.execution_time else "N/A")
        table.add_row("Final Transcript", workflow_result.final_transcript_path or "Not generated")
        table.add_row("Quality Summary", workflow_result.quality_summary_path or "Not generated")
        
        if workflow_result.quality_metrics:
            table.add_row("Quality Score", f"{workflow_result.quality_metrics.get('quality_score', 0):.2f}")
            table.add_row("Total Issues", str(workflow_result.quality_metrics.get('total_issues', 0)))
            table.add_row("Error Count", str(workflow_result.quality_metrics.get('error_count', 0)))
        
        if workflow_result.errors:
            table.add_row("Errors", f"{len(workflow_result.errors)} errors encountered")
        
        self.console.print(table)


class TranscriptGeneratorCLI:
    """Main CLI application for transcript generation"""
    
    def __init__(self):
        self.formatter = CLIFormatter()
        self.console = Console()
        self.setup_logging()
    
    def setup_logging(self):
        """Configure logging for CLI"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('transcript_generator.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def validate_environment(self) -> bool:
        """Validate required environment variables"""
        self.formatter.print_phase("Environment Validation", "Checking required environment variables...")
        
        required_vars = ["OPENAI_API_KEY"]
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.formatter.print_error(f"Missing environment variables: {', '.join(missing_vars)}")
            self.formatter.print_info("Create a .env file with required variables or set them manually")
            self.formatter.print_info("Example .env content:")
            self.formatter.print_info("OPENAI_API_KEY=your_openai_api_key_here")
            return False
        
        self.formatter.print_success("All required environment variables are set")
        return True
    
    async def validate_knowledge_base(self, output_dir: str) -> bool:
        """Validate knowledge base availability and health"""
        self.formatter.print_phase("Knowledge Base Validation", "Checking knowledge base availability...")
        
        try:
            # Check Knowledge Bridge MCP Server (use knowledge_db, not output_dir)
            knowledge_db_dir = "knowledge_db"  # Separate from output_dir
            knowledge_mcp_server = create_knowledge_mcp_server(knowledge_db_dir)
            health = knowledge_mcp_server.health_check()
            
            if health.get("server_status") != "healthy":
                self.formatter.print_error("Knowledge Bridge MCP server not healthy")
                self.formatter.print_info("Run training manager first: poetry run python run_training_manager.py --course-path <course-path>")
                return False
            
            accessor_health = health.get("content_accessor", {})
            available_courses = accessor_health.get("available_courses", 0)
            total_modules = accessor_health.get("total_modules", 0)
            
            if available_courses == 0:
                self.formatter.print_error("No preprocessed training data found")
                self.formatter.print_info("Run training manager first to preprocess course data")
                return False
            
            self.formatter.print_success(f"Knowledge base ready: {available_courses} courses, {total_modules} modules")
            return True
            
        except Exception as e:
            self.formatter.print_error(f"Knowledge base validation failed: {e!s}")
            return False
    
    def validate_syllabus(self, syllabus_path: str) -> dict[str, Any] | None:
        """Validate and load syllabus file"""
        self.formatter.print_phase("Syllabus Validation", f"Loading syllabus from {syllabus_path}")
        
        try:
            if not os.path.exists(syllabus_path):
                self.formatter.print_error(f"Syllabus file not found: {syllabus_path}")
                return None
            
            # Load syllabus using existing loader
            syllabus_modules = load_syllabus(syllabus_path)
            
            # Transform to WorkflowOrchestrator compatible structure
            sections = transform_syllabus_structure(syllabus_modules)
            
            # Convert to structured format for WorkflowOrchestrator
            syllabus = {
                "course_title": "AI Engineer Basic Course",  # Default title
                "sections": sections,  # Fix: use "sections" instead of "modules"
                "source_file": syllabus_path
            }
            
            self.formatter.print_success(f"Syllabus loaded: {len(sections)} sections found")
            
            # Display sections (updated table title and content)
            table = Table(title="📚 Course Sections")
            table.add_column("Section", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("Section ID", style="magenta")
            
            for i, section in enumerate(sections, 1):
                if isinstance(section, dict):
                    table.add_row(
                        f"Section {i}", 
                        section.get('title', 'Untitled'),
                        section.get('section_id', 'unknown')
                    )
                else:
                    table.add_row(f"Section {i}", str(section), "unknown")
            
            self.console.print(table)
            return syllabus
            
        except Exception as e:
            self.formatter.print_error(f"Syllabus validation failed: {e!s}")
            return None
    
    def setup_output_directories(self, base_output_dir: str) -> dict[str, str]:
        """Setup and create output directories"""
        self.formatter.print_phase("Directory Setup", "Creating output directories...")
        
        directories = {
            "output": base_output_dir,
            "research_notes": os.path.join(base_output_dir, "research_notes"),
            "chapter_drafts": os.path.join(base_output_dir, "chapter_drafts"),
            "quality_issues": os.path.join(base_output_dir, "quality_issues"),
            "logs": os.path.join(base_output_dir, "logs")
        }
        
        for name, path in directories.items():
            os.makedirs(path, exist_ok=True)
            self.formatter.print_success(f"Created {name} directory: {path}")
        
        return directories
    
    async def execute_workflow(self, syllabus: dict[str, Any], directories: dict[str, str], config: dict[str, Any]) -> WorkflowResult:
        """Execute the complete transcript generation workflow"""
        self.formatter.print_phase("Workflow Execution", "Starting complete transcript generation pipeline...")
        
        # Configure WorkflowOrchestrator
        workflow_config = WorkflowConfig(
            output_dir=directories["output"],
            research_output_dir=directories["research_notes"],
            quality_output_dir=directories["quality_issues"],
            overwrite_existing=config.get("overwrite", False),
            max_retries=config.get("max_retries", 3),
            timeout_per_phase=config.get("timeout_per_phase", 300),
            continue_on_errors=config.get("continue_on_errors", True),
            enable_progress_tracking=True
        )
        
        # Initialize orchestrator
        orchestrator = WorkflowOrchestrator(workflow_config)
        
        # Execute pipeline with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            
            task = progress.add_task("Executing workflow...", total=100)
            
            try:
                # Execute the complete pipeline
                result = await orchestrator.execute_pipeline(syllabus)
                progress.update(task, completed=100)
                
                return result
                
            except Exception as e:
                self.formatter.print_error(f"Workflow execution failed: {e!s}")
                return WorkflowResult(
                    success=False,
                    errors=[f"{e!s}"]
                )
    
    def generate_execution_report(self, workflow_result: WorkflowResult, directories: dict[str, str], syllabus: dict[str, Any]):
        """Generate comprehensive execution report"""
        self.formatter.print_phase("Execution Report", "Generating comprehensive execution report...")
        
        # Create report data
        report = {
            "execution_metadata": {
                "timestamp": datetime.now().isoformat(),
                "success": workflow_result.success,
                "execution_time": workflow_result.execution_time,
                "syllabus_source": syllabus.get("source_file"),
                "course_title": syllabus.get("course_title"),
                "section_count": len(syllabus.get("sections", []))
            },
            "output_files": {
                "final_transcript": workflow_result.final_transcript_path,
                "quality_summary": workflow_result.quality_summary_path,
                "research_notes_dir": directories["research_notes"],
                "quality_issues_dir": directories["quality_issues"]
            },
            "quality_metrics": workflow_result.quality_metrics or {},
            "errors": workflow_result.errors or []
        }
        
        # Save report
        report_path = os.path.join(directories["output"], "execution_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.formatter.print_success(f"Execution report saved: {report_path}")
        
        # Display results
        self.formatter.print_results_table(workflow_result)
        
        return report_path


@click.command()
@click.option('--syllabus', '-s', required=True, help='Path to syllabus file (required)')
@click.option('--output-dir', '-o', default='output', help='Output directory for generated files')
@click.option('--config', '-c', help='Path to configuration file (optional)')
@click.option('--overwrite', is_flag=True, help='Overwrite existing output files')
@click.option('--max-retries', default=3, help='Maximum retries per workflow phase')
@click.option('--timeout', default=300, help='Timeout per phase in seconds')
@click.option('--continue-on-errors', is_flag=True, default=True, help='Continue workflow on non-critical errors')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--dry-run', is_flag=True, help='Validate inputs without executing workflow')
def main(syllabus, output_dir, config, overwrite, max_retries, timeout, continue_on_errors, verbose, dry_run):
    """
    GenAI Training Transcript Generator CLI
    
    Generate training course transcripts from syllabus using complete AI-powered workflow.
    Orchestrates Research Team → Editing Team → Editorial Finalizer pipeline.
    
    Example:
        transcript-generator --syllabus syllabus.md --output-dir output
    """
    
    # Initialize CLI
    cli = TranscriptGeneratorCLI()
    cli.formatter.print_header("End-to-End CLI Integration (US-009)")
    
    # Configure logging level
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        cli.formatter.print_info("Verbose logging enabled")
    
    # Load additional configuration if provided
    cli_config = {
        "overwrite": overwrite,
        "max_retries": max_retries,
        "timeout_per_phase": timeout,
        "continue_on_errors": continue_on_errors
    }
    
    if config:
        try:
            with open(config) as f:
                file_config = yaml.safe_load(f)
                cli_config.update(file_config)
            cli.formatter.print_success(f"Configuration loaded from {config}")
        except Exception as e:
            cli.formatter.print_warning(f"Could not load config file: {e}")
    
    async def run_workflow():
        """Async workflow execution"""
        try:
            # 1. Validate environment variables
            if not cli.validate_environment():
                cli.formatter.print_error("Environment validation failed. Aborting.")
                return False
            
            # 2. Validate knowledge base
            if not await cli.validate_knowledge_base(output_dir):
                cli.formatter.print_error("Knowledge base validation failed. Aborting.")
                return False
            
            # 3. Validate syllabus
            syllabus_data = cli.validate_syllabus(syllabus)
            if not syllabus_data:
                cli.formatter.print_error("Syllabus validation failed. Aborting.")
                return False
            
            # 4. Setup directories
            directories = cli.setup_output_directories(output_dir)
            
            if dry_run:
                cli.formatter.print_success("Dry run completed successfully. All validations passed.")
                return True
            
            # 5. Execute workflow
            workflow_result = await cli.execute_workflow(syllabus_data, directories, cli_config)
            
            # 6. Generate report
            report_path = cli.generate_execution_report(workflow_result, directories, syllabus_data)
            
            if workflow_result.success:
                cli.formatter.print_success("🎉 Workflow completed successfully!")
                cli.formatter.print_info(f"📄 Final transcript: {workflow_result.final_transcript_path}")
                cli.formatter.print_info(f"📊 Quality summary: {workflow_result.quality_summary_path}")
                cli.formatter.print_info(f"📋 Execution report: {report_path}")
            else:
                cli.formatter.print_error("Workflow completed with errors. Check logs for details.")
                if workflow_result.errors:
                    for error in workflow_result.errors:
                        cli.formatter.print_error(f"  • {error}")
            
            return workflow_result.success
            
        except KeyboardInterrupt:
            cli.formatter.print_warning("Workflow interrupted by user")
            return False
        except Exception as e:
            cli.formatter.print_error(f"Unexpected error: {e!s}")
            cli.logger.exception("Unexpected error in workflow execution")
            return False
    
    # Run async workflow
    try:
        success = asyncio.run(run_workflow())
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except Exception as e:
        cli.formatter.print_error(f"CLI execution failed: {e!s}")
        sys.exit(1)


if __name__ == "__main__":
    main()