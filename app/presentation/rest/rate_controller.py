"""REST: керування швидкістю генератора з UI (слайдер)."""
from __future__ import annotations

from fastapi import APIRouter

from app.application.dto.monitoring import RateConfigDto
from app.application.ports.inbound.configure_rate import ConfigureRate


class RateController:
    def __init__(self, configure_rate: ConfigureRate) -> None:
        self._configure_rate = configure_rate
        self.router = APIRouter(prefix="/api/rate", tags=["rate"])
        self.router.add_api_route("", self.set_rate, methods=["PUT"], response_model=RateConfigDto)

    async def set_rate(self, config: RateConfigDto) -> RateConfigDto:
        """PUT /api/rate {"rate": 500} -> запис config:rate у Redis."""
        raise NotImplementedError
