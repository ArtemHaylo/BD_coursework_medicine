"""REST: аналоги препарату (запити №4, №5)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query

from app.application.dto.analogue import AnalogueDto
from app.application.ports.inbound.get_analogues import GetAnalogues


class AnaloguesController:
    def __init__(self, get_analogues: GetAnalogues) -> None:
        self._get_analogues = get_analogues
        self.router = APIRouter(prefix="/api/medicines", tags=["analogues"])
        self.router.add_api_route("/{medicine_id}/analogues", self.analogues, methods=["GET"],
                                  response_model=list[AnalogueDto])

    async def analogues(
        self,
        medicine_id: UUID,
        depth: int = Query(1, ge=1, le=2),
        exclude_symptom: list[str] = Query(default=[]),
    ) -> list[AnalogueDto]:
        """GET /api/medicines/{id}/analogues?depth=1&exclude_symptom=nausea"""
        raise NotImplementedError
