"""Session management for Evernote chatbot with conversation history."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import ChatbotConfig


class ChatSession:
    """Manages conversation history and session state."""

    def __init__(
        self,
        config: ChatbotConfig,
        save_history: bool = True,
        history_file: str | None = None,
    ):
        self.config = config
        self.save_history = save_history
        self.messages: list[dict[str, Any]] = []
        self.session_start = datetime.now()

        # Set up history file
        if history_file:
            self.history_file = Path(history_file)
        elif save_history:
            # Default to user's home directory
            home_dir = Path.home()
            self.history_file = home_dir / ".evernote_chatbot_history.json"
        else:
            self.history_file = None

        # Load existing history if available
        if self.save_history and self.history_file:
            self._load_history()

    def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation history."""
        message = {
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        self.messages.append(message)
        self._save_if_enabled()

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the conversation history."""
        message = {
            "role": "assistant",
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        self.messages.append(message)
        self._save_if_enabled()

    def add_system_message(self, content: str) -> None:
        """Add a system message to the conversation history."""
        message = {
            "role": "system",
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        self.messages.append(message)
        self._save_if_enabled()

    def get_recent_messages(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get the most recent messages."""
        return self.messages[-limit:] if self.messages else []

    def get_user_queries(self) -> list[str]:
        """Get all user queries from the session."""
        return [
            msg["content"] for msg in self.messages
            if msg["role"] == "user"
        ]

    def get_context_summary(self) -> str:
        """Get a summary of the current conversation context."""
        if not self.messages:
            return "No conversation history."

        user_messages = len([msg for msg in self.messages if msg["role"] == "user"])
        assistant_messages = len([msg for msg in self.messages if msg["role"] == "assistant"])

        recent_queries = self.get_user_queries()[-3:]  # Last 3 queries

        summary_parts = [
            f"Session started: {self.session_start.strftime('%Y-%m-%d %H:%M')}",
            f"Messages: {user_messages} from user, {assistant_messages} responses",
        ]

        if recent_queries:
            summary_parts.append(f"Recent queries: {'; '.join(recent_queries)}")

        return " | ".join(summary_parts)

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.messages = []
        self.session_start = datetime.now()
        self._save_if_enabled()

    def save_session_history(self) -> bool:
        """Save conversation history to file."""
        if not self.save_history or not self.history_file:
            return False

        if not self.messages:
            return False

        try:
            # Prepare data to save
            session_data = {
                "session_start": self.session_start.isoformat(),
                "session_end": datetime.now().isoformat(),
                "config": {
                    "container_name": self.config.container_name,
                    "max_notes_per_query": self.config.max_notes_per_query,
                    "allowed_notebooks": list(self.config.allowed_notebooks),
                    "prefer_html": self.config.prefer_html,
                },
                "messages": self.messages,
                "total_messages": len(self.messages),
                "user_messages": len([m for m in self.messages if m["role"] == "user"]),
                "assistant_messages": len([m for m in self.messages if m["role"] == "assistant"]),
            }

            # Ensure parent directory exists
            self.history_file.parent.mkdir(parents=True, exist_ok=True)

            # Load existing history to merge
            existing_sessions = []
            if self.history_file.exists():
                try:
                    with open(self.history_file, encoding='utf-8') as f:
                        data = json.load(f)
                        existing_sessions = data.get("sessions", [])
                except (json.JSONDecodeError, KeyError):
                    # If file is corrupted, start fresh
                    existing_sessions = []

            # Add current session
            existing_sessions.append(session_data)

            # Keep only recent sessions (last 50)
            existing_sessions = existing_sessions[-50:]

            # Save to file
            history_data = {
                "last_updated": datetime.now().isoformat(),
                "total_sessions": len(existing_sessions),
                "sessions": existing_sessions,
            }

            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception:
            return False

    def _load_history(self) -> bool:
        """Load conversation history from file."""
        if not self.history_file or not self.history_file.exists():
            return False

        try:
            with open(self.history_file, encoding='utf-8') as f:
                data = json.load(f)

            sessions = data.get("sessions", [])
            if not sessions:
                return False

            # Load the most recent session
            last_session = sessions[-1]

            # Only load if it's from today (to avoid loading old sessions)
            try:
                session_start = datetime.fromisoformat(last_session["session_start"])
                if session_start.date() == datetime.now().date():
                    self.messages = last_session.get("messages", [])
                    self.session_start = session_start
                    return True
            except (ValueError, KeyError):
                pass

            return False

        except Exception:
            return False

    def _save_if_enabled(self) -> None:
        """Save history if saving is enabled."""
        if self.save_history:
            self.save_session_history()

    def export_to_file(self, filepath: str, format: str = "json") -> bool:
        """
        Export conversation history to a file.

        Args:
            filepath: Path to save the file
            format: Export format ('json', 'txt', 'md')

        Returns:
            True if successful, False otherwise
        """
        try:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)

            if format.lower() == "json":
                return self._export_json(filepath)
            elif format.lower() == "txt":
                return self._export_txt(filepath)
            elif format.lower() == "md":
                return self._export_markdown(filepath)
            else:
                return False

        except Exception:
            return False

    def _export_json(self, filepath: Path) -> bool:
        """Export to JSON format."""
        data = {
            "session_start": self.session_start.isoformat(),
            "export_time": datetime.now().isoformat(),
            "messages": self.messages,
            "config_summary": self.config.to_display_dict(),
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return True

    def _export_txt(self, filepath: Path) -> bool:
        """Export to plain text format."""
        lines = [
            "Evernote Chatbot Conversation History",
            f"Session started: {self.session_start.strftime('%Y-%m-%d %H:%M')}",
            f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "=" * 50,
            "",
        ]

        for i, message in enumerate(self.messages, 1):
            role = message["role"].title()
            timestamp = message.get("timestamp", "Unknown")
            content = message["content"]

            lines.extend([
                f"{i}. [{role}] - {timestamp}",
                content,
                "",
            ])

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        return True

    def _export_markdown(self, filepath: Path) -> bool:
        """Export to Markdown format."""
        lines = [
            "# Evernote Chatbot Conversation History",
            "",
            f"**Session started:** {self.session_start.strftime('%Y-%m-%d %H:%M')}  ",
            f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
        ]

        current_date = None
        for message in self.messages:
            # Parse timestamp
            try:
                msg_time = datetime.fromisoformat(message.get("timestamp", ""))
                msg_date = msg_time.strftime("%Y-%m-%d")

                # Add date header if changed
                if msg_date != current_date:
                    lines.extend(["", f"## {msg_date}", ""])
                    current_date = msg_date

                time_str = msg_time.strftime("%H:%M")
            except (ValueError, TypeError):
                time_str = "Unknown time"

            role = "**You**" if message["role"] == "user" else "**Assistant**"
            lines.extend([
                f"### {role} - {time_str}",
                "",
                message["content"],
                "",
            ])

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        return True