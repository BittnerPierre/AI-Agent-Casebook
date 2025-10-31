"""Progress indicator system with spinners and logging for Evernote chatbot."""

import logging
import time
from pathlib import Path
from typing import Any

from rich.console import Console, Group
from rich.live import Live
from rich.spinner import Spinner


class ProgressTracker:
    """Tracks progress with spinners for user feedback and detailed logging."""

    def __init__(self, console: Console, log_file: Path | None = None):
        self.console = console
        self.live = Live(console=console, auto_refresh=True)
        self.items: dict[str, tuple[str, bool, bool]] = {}  # content, is_done, hide_when_done
        self.start_times: dict[str, float] = {}

        # Setup logging
        self.logger = self._setup_logger(log_file)

    def _setup_logger(self, log_file: Path | None) -> logging.Logger:
        """Setup file logger for debug information."""
        logger = logging.getLogger("evernote_chatbot")
        logger.setLevel(logging.INFO)

        # Clear existing handlers to avoid duplicates
        logger.handlers.clear()

        if log_file:
            # Ensure log directory exists
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # File handler for debug logs (without emojis)
            file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        return logger

    def start(self) -> None:
        """Start the live display."""
        self.live.start()
        self.logger.info("Progress tracker started")

    def stop(self) -> None:
        """Stop the live display."""
        self.live.stop()
        self.logger.info("Progress tracker stopped")

    def start_task(self, task_id: str, message: str, hide_when_done: bool = True) -> None:
        """Start a new task with spinner."""
        self.items[task_id] = (message, False, hide_when_done)
        self.start_times[task_id] = time.time()
        self.logger.info(f"Started task '{task_id}': {message}")
        self._update_display()

    def update_task(self, task_id: str, message: str) -> None:
        """Update task message while keeping it active."""
        if task_id in self.items:
            _, is_done, hide_when_done = self.items[task_id]
            self.items[task_id] = (message, is_done, hide_when_done)
            self.logger.info(f"Updated task '{task_id}': {message}")
            self._update_display()

    def complete_task(self, task_id: str, final_message: str | None = None) -> None:
        """Mark task as completed."""
        if task_id in self.items:
            original_message, _, hide_when_done = self.items[task_id]
            message = final_message or original_message
            self.items[task_id] = (message, True, hide_when_done)

            # Log completion with timing
            elapsed = time.time() - self.start_times.get(task_id, time.time())
            self.logger.info(f"Completed task '{task_id}' in {elapsed:.2f}s: {message}")

            self._update_display()

    def fail_task(self, task_id: str, error_message: str) -> None:
        """Mark task as failed."""
        if task_id in self.items:
            self.items[task_id] = (f"❌ {error_message}", True, False)  # Show failures

            elapsed = time.time() - self.start_times.get(task_id, time.time())
            self.logger.error(f"Failed task '{task_id}' after {elapsed:.2f}s: {error_message}")

            self._update_display()

    def log_info(self, message: str) -> None:
        """Log info message without showing in UI."""
        self.logger.info(message)

    def log_debug(self, message: str) -> None:
        """Log debug message without showing in UI."""
        self.logger.debug(message)

    def log_error(self, message: str) -> None:
        """Log error message without showing in UI."""
        self.logger.error(message)

    def _update_display(self) -> None:
        """Update the live display with current tasks."""
        renderables: list[Any] = []

        for task_id, (message, is_done, hide_when_done) in self.items.items():
            if is_done:
                if not hide_when_done:
                    # Show completed tasks that shouldn't be hidden
                    if message.startswith("❌"):
                        renderables.append(message)  # Show errors
                    else:
                        renderables.append(f"✅ {message}")
            else:
                # Show active tasks with spinner
                renderables.append(Spinner("dots", text=message))

        if renderables:
            self.live.update(Group(*renderables))
        else:
            # Clear display if no active tasks
            self.live.update("")

    def clear_completed_tasks(self) -> None:
        """Remove all completed tasks from display."""
        self.items = {
            task_id: data for task_id, data in self.items.items()
            if not data[1]  # Keep only non-completed tasks
        }
        self._update_display()

    def show_final_result(self, content: Any) -> None:
        """Show final result and clear all progress indicators."""
        self.live.stop()
        self.console.print(content)
        self.logger.info("Displayed final result")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()