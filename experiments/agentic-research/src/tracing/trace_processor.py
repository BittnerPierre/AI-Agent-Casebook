import logging
import logging.handlers
import json
import queue
from datetime import datetime
from pathlib import Path
from typing import Any

from agents import TracingProcessor, Trace, Span

class FileTraceProcessor(TracingProcessor):
    """
    Processeur de tracing simple qui log tous les événements dans un fichier.
    """
    
    def __init__(self, log_dir: str = "traces", log_file: str = None):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"trace_log_{timestamp}.log"
        
        self.log_file_path = self.log_dir / log_file
        
        # Logger asynchrone pour performance
        self.logger = logging.getLogger("FileTraceProcessor")
        
        # Queue pour logging asynchrone
        self.log_queue = queue.Queue()
        
        # Handler qui écrit réellement sur disque
        file_handler = logging.FileHandler(self.log_file_path)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        
        # Queue handler pour performance (non-bloquant)
        queue_handler = logging.handlers.QueueHandler(self.log_queue)
        
        # Listener qui gère l'écriture en arrière-plan
        self.queue_listener = logging.handlers.QueueListener(
            self.log_queue, file_handler, respect_handler_level=True
        )
        self.queue_listener.start()
        
        if not self.logger.handlers:
            self.logger.addHandler(queue_handler)
            self.logger.setLevel(logging.INFO)
    
    def on_trace_start(self, trace: Trace) -> None:
        data = {
            "event": "trace_start",
            "trace_id": trace.trace_id,
            "name": trace.name,
            "exported_data": trace.export()
        }
        self.logger.info(json.dumps(data))
    
    def on_trace_end(self, trace: Trace) -> None:
        data = {
            "event": "trace_end", 
            "trace_id": trace.trace_id,
            "name": trace.name,
            "exported_data": trace.export()
        }
        self.logger.info(json.dumps(data))
    
    def on_span_start(self, span: Span[Any]) -> None:
        data = {
            "event": "span_start",
            "span_id": span.span_id,
            "trace_id": span.trace_id,
            "parent_id": span.parent_id,
            "started_at": str(span.started_at) if span.started_at else None,
            "exported_data": span.export()
        }
        self.logger.info(json.dumps(data))
    
    def on_span_end(self, span: Span[Any]) -> None:
        data = {
            "event": "span_end",
            "span_id": span.span_id,
            "trace_id": span.trace_id,
            "parent_id": span.parent_id,
            "started_at": str(span.started_at) if span.started_at else None,
            "ended_at": str(span.ended_at) if span.ended_at else None,
            "exported_data": span.export()
        }
        self.logger.info(json.dumps(data))
    
    def shutdown(self, timeout: float | None = None) -> None:
        # Arrêter le listener asynchrone proprement
        if hasattr(self, 'queue_listener'):
            self.queue_listener.stop()
        
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)
    
    def force_flush(self) -> None:
        # Force le flush de la queue vers le disque
        if hasattr(self, 'log_queue'):
            # Attendre que la queue soit vide
            self.log_queue.join() if hasattr(self.log_queue, 'join') else None
        
        for handler in self.logger.handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
