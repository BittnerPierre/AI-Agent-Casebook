import logging
import logging.handlers
import queue
from datetime import datetime
from pathlib import Path
from typing import Any

from agents import Span, Trace, TracingProcessor


class FileTraceProcessor(TracingProcessor):
    """
    Processeur de tracing amélioré qui log tous les événements dans un fichier avec rotation.

    Améliorations :
    - Ne pollue pas la console (log uniquement dans le fichier)
    - Rotation automatique des fichiers (max 10 fichiers de 10MB chacun)
    - Limite le nombre de logs par fichier
    - Nettoyage automatique des anciens fichiers
    """

    def __init__(
        self,
        log_dir: str = "traces",
        log_file: str = None,
        max_files: int = 10,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
    ):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"trace_log_{timestamp}.log"

        self.log_file_path = self.log_dir / log_file
        self.max_files = max_files
        self.max_bytes = max_bytes
        self.backup_count = backup_count

        # Logger asynchrone pour performance - SANS console output
        self.logger = logging.getLogger("FileTraceProcessor")

        # IMPORTANT: Désactiver la propagation vers la console
        self.logger.propagate = False

        # Queue pour logging asynchrone
        self.log_queue = queue.Queue()

        # Handler avec rotation automatique (comme log4j)
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file_path,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding="utf-8",
        )

        # Formatter plus compact
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)

        # Queue handler pour performance (non-bloquant)
        queue_handler = logging.handlers.QueueHandler(self.log_queue)

        # Listener qui gère l'écriture en arrière-plan
        self.queue_listener = logging.handlers.QueueListener(
            self.log_queue, file_handler, respect_handler_level=True
        )
        self.queue_listener.start()

        # Nettoyer les anciens fichiers de trace
        self._cleanup_old_trace_files()

        if not self.logger.handlers:
            self.logger.addHandler(queue_handler)
            self.logger.setLevel(logging.INFO)

    def _cleanup_old_trace_files(self) -> None:
        """
        Nettoie les anciens fichiers de trace pour éviter l'accumulation.
        Garde seulement les max_files plus récents.
        """
        try:
            # Trouver tous les fichiers de trace
            trace_files = list(self.log_dir.glob("trace_log_*.log*"))

            if len(trace_files) > self.max_files:
                # Trier par date de modification (plus récent en premier)
                trace_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

                # Supprimer les fichiers en trop
                files_to_delete = trace_files[self.max_files :]
                for file_path in files_to_delete:
                    try:
                        file_path.unlink()
                        print(f"🗑️  Fichier de trace supprimé: {file_path.name}")
                    except Exception as e:
                        print(f"⚠️  Impossible de supprimer {file_path.name}: {e}")
        except Exception as e:
            print(f"⚠️  Erreur lors du nettoyage des fichiers de trace: {e}")

    def _safe_export_data(self, export_func) -> str:
        """
        Exporte les données de manière sécurisée en chaîne de caractères.
        """
        try:
            exported_data = export_func()
            return str(exported_data)
        except Exception as e:
            return f"<Export failed: {type(e).__name__}: {e}>"

    def _log_event(self, data: dict) -> None:
        """
        Log un événement en format simple et lisible.
        """
        try:
            # Format plus compact et lisible
            event_str = f"EVENT: {data['event']}"
            if "trace_id" in data:
                event_str += f" | TRACE: {data['trace_id']}"
            if "span_id" in data:
                event_str += f" | SPAN: {data['span_id']}"
            if "name" in data:
                event_str += f" | NAME: {data['name']}"
            if "started_at" in data:
                event_str += f" | STARTED: {data['started_at']}"
            if "ended_at" in data:
                event_str += f" | ENDED: {data['ended_at']}"
            if "exported_data" in data:
                # Limiter la taille des données exportées pour éviter les logs trop longs
                exported_str = str(data["exported_data"])
                if len(exported_str) > 500:
                    exported_str = exported_str[:500] + "..."
                event_str += f" | DATA: {exported_str}"

            self.logger.info(event_str)
        except Exception as e:
            # En cas d'échec, log brut
            self.logger.error(f"CRITICAL: Failed to log event. Error: {e}. Raw data: {data}")

    def on_trace_start(self, trace: Trace) -> None:
        data = {
            "event": "trace_start",
            "trace_id": trace.trace_id,
            "name": trace.name,
            "exported_data": self._safe_export_data(trace.export),
        }
        self._log_event(data)

    def on_trace_end(self, trace: Trace) -> None:
        data = {
            "event": "trace_end",
            "trace_id": trace.trace_id,
            "name": trace.name,
            "exported_data": self._safe_export_data(trace.export),
        }
        self._log_event(data)

    def on_span_start(self, span: Span[Any]) -> None:
        data = {
            "event": "span_start",
            "span_id": span.span_id,
            "trace_id": span.trace_id,
            "parent_id": span.parent_id,
            "started_at": str(span.started_at) if span.started_at else None,
            "exported_data": self._safe_export_data(span.export),
        }
        self._log_event(data)

    def on_span_end(self, span: Span[Any]) -> None:
        data = {
            "event": "span_end",
            "span_id": span.span_id,
            "trace_id": span.trace_id,
            "parent_id": span.parent_id,
            "started_at": str(span.started_at) if span.started_at else None,
            "ended_at": str(span.ended_at) if span.ended_at else None,
            "exported_data": self._safe_export_data(span.export),
        }
        self._log_event(data)

    def get_log_file_path(self) -> Path:
        """
        Retourne le chemin du fichier de log actuel.
        Utile pour consulter les logs quand nécessaire.
        """
        return self.log_file_path

    def show_recent_logs(self, lines: int = 20) -> None:
        """
        Affiche les logs récents dans la console pour debug.
        """
        try:
            if self.log_file_path.exists():
                with open(self.log_file_path, encoding="utf-8") as f:
                    all_lines = f.readlines()
                    recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                    print(f"\n📋 {lines} derniers logs de {self.log_file_path.name}:")
                    print("=" * 80)
                    for line in recent_lines:
                        print(line.rstrip())
                    print("=" * 80)
            else:
                print(f"📋 Aucun fichier de log trouvé: {self.log_file_path}")
        except Exception as e:
            print(f"⚠️  Erreur lors de la lecture des logs: {e}")

    def shutdown(self, timeout: float | None = None) -> None:
        # Arrêter le listener asynchrone proprement
        if hasattr(self, "queue_listener"):
            self.queue_listener.stop()

        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)

    def force_flush(self) -> None:
        # Force le flush de la queue vers le disque
        if hasattr(self, "log_queue"):
            # Attendre que la queue soit vide
            self.log_queue.join() if hasattr(self.log_queue, "join") else None

        for handler in self.logger.handlers:
            if hasattr(handler, "flush"):
                handler.flush()
