"""Вхідний порт: приймання пакета документів (шлях команд)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dto.ingest import IngestBatchDto, IngestResultDto


class IngestDocument(ABC):
    @abstractmethod
    async def handle(self, batch: IngestBatchDto) -> IngestResultDto: ...
