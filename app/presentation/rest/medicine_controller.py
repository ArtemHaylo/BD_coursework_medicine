"""REST: CRUD препаратів + фільтрація (запити №2, №3)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query

from app.application.dto.medicine import (
    MedicineCard, MedicineCreateDto, MedicineListResult, MedicineUpdateDto,
)
from app.application.ports.inbound import (
    CreateMedicine, DeleteMedicine, GetMedicineCard, ListMedicines, UpdateMedicine,
)


class MedicineController:
    def __init__(self, list_medicines: ListMedicines, get_card: GetMedicineCard,
                 create_medicine: CreateMedicine, update_medicine: UpdateMedicine,
                 delete_medicine: DeleteMedicine) -> None:
        self._list = list_medicines
        self._get_card = get_card
        self._create = create_medicine
        self._update = update_medicine
        self._delete = delete_medicine
        self.router = APIRouter(prefix="/api/medicines", tags=["medicines"])
        r = self.router
        r.add_api_route("", self.list_medicines, methods=["GET"], response_model=MedicineListResult)
        r.add_api_route("/{medicine_id}", self.get_card, methods=["GET"], response_model=MedicineCard)
        r.add_api_route("", self.create, methods=["POST"], response_model=MedicineCard, status_code=201)
        r.add_api_route("/{medicine_id}", self.update, methods=["PATCH"], response_model=MedicineCard)
        r.add_api_route("/{medicine_id}", self.delete, methods=["DELETE"], status_code=204)

    async def list_medicines(
        self,
        is_prescription: bool | None = None,
        price_max: float | None = None,
        therapeutic_class: str | None = None,
        chemical_class: str | None = None,
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
    ) -> MedicineListResult:
        raise NotImplementedError

    async def get_card(self, medicine_id: UUID) -> MedicineCard:
        """404, якщо препарату немає (MedicineNotFoundError)."""
        raise NotImplementedError

    async def create(self, dto: MedicineCreateDto) -> MedicineCard:
        raise NotImplementedError

    async def update(self, medicine_id: UUID, dto: MedicineUpdateDto) -> MedicineCard:
        raise NotImplementedError

    async def delete(self, medicine_id: UUID) -> None:
        raise NotImplementedError
