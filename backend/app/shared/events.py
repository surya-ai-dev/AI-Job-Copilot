# backend/app/shared/events.py
# Shared Domain Events definition representing events triggered throughout the pipeline

from dataclasses import dataclass
from datetime import datetime
import uuid
from typing import Callable, Dict, List

@dataclass
class DomainEvent:
    event_id: uuid.UUID
    timestamp: datetime
    event_name: str


@dataclass
class JobParsedEvent(DomainEvent):
    user_id: uuid.UUID
    job_id: uuid.UUID
    company_name: str
    job_title: str


@dataclass
class JobAnalyzedEvent(DomainEvent):
    user_id: uuid.UUID
    job_id: uuid.UUID
    analysis_id: uuid.UUID


@dataclass
class ResumeOptimizedEvent(DomainEvent):
    user_id: uuid.UUID
    resume_id: uuid.UUID
    optimization_id: uuid.UUID
    match_score: int


@dataclass
class EmailGeneratedEvent(DomainEvent):
    user_id: uuid.UUID
    draft_id: uuid.UUID
    recipient_email: str


@dataclass
class EmailSentEvent(DomainEvent):
    user_id: uuid.UUID
    history_id: uuid.UUID
    recipient_email: str


@dataclass
class ApplicationSavedEvent(DomainEvent):
    user_id: uuid.UUID
    application_id: uuid.UUID
    company_name: str


class EventDispatcher:
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def register(self, event_name: str, listener: Callable) -> None:
        """Register listener for a domain event."""
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(listener)

    def dispatch(self, event: DomainEvent) -> None:
        """Broadcast event to all registered listeners."""
        event_name = event.event_name
        if event_name in self._listeners:
            for listener in self._listeners[event_name]:
                try:
                    listener(event)
                except Exception as e:
                    print(f"Error handling event {event_name}: {e}")

# Global instance dispatcher
dispatcher = EventDispatcher()
