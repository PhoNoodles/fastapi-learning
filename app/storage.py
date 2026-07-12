from fastapi import HTTPException, status
from uuid import UUID

from app.models import ItemResponse


items: list[ItemResponse] = []


def find_item(item_id: UUID) -> ItemResponse:
    for item in items:
        if item.item_id == item_id:
            return item

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Item {item_id} not found",
    )