# backend/app/core/logging.py
# Structured logging configurations mapping to JSON output formatting with correlation tracer IDs

import logging
import json
import uuid
from contextvars import ContextVar
from datetime import datetime

# Context variable tracking correlation trace IDs across threads
correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")

class StructuredJSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        """Serialize log records to clean JSON structure."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id.get(),
            "file": record.filename,
            "line": record.lineno
        }
        # Add extra properties if available
        if hasattr(record, "extra_payload"):
            log_data["extra"] = record.extra_payload
            
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)


def setup_structured_logging():
    """Register structured JSON logging configs."""
    root_logger = logging.getLogger()
    
    # Exclude redundant handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler()
    formatter = StructuredJSONFormatter()
    handler.setFormatter(formatter)
    
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

# Run logger configurations setup
setup_structured_logging()
logger = logging.getLogger("AIJobCopilot")
