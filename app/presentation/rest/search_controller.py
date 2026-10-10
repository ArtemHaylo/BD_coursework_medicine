"""REST: пошук препаратів (запит №1)."""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.application.dto.search import SearchQuery, SearchResult
from app.application.ports.inbound.search_medicines import SearchMedicines


class SearchController:
    def __init__(self, search_medicines: SearchMedicines) -> None:
        self._search = search_medicines
        self.router = APIRouter(prefix="/api", tags=["search"])
        self.router.add_api_route("/search", self.search, methods=["GET"],
                                  response_model=SearchResult)

    async def search(
        self,
        q: str = Query(..., min_length=1, description="Текст запиту"),
        is_prescription: bool | None = None,
        price_max: float | None = None,
        limit: int = Query(20, ge=1, le=100),
    ) -> SearchResult:
        """GET /api/search?q=...  Збирає SearchQuery і викликає вхідний порт."""
        raise NotImplementedError
