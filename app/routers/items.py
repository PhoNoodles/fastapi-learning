from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Path,
    Query,
    Response,
    status,
)

from app.models import (
    Item,
    ItemActionResponse,
    ItemResponse,
    ItemUpdate,
)
from app.settings import settings
from app.storage import find_item, items


router = APIRouter(
    prefix="/items",
    tags=["Items"],
)

@router.post(
    "",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_item(item: Item) -> ItemResponse:
    current_time = datetime.now(timezone.utc)

    new_item = ItemResponse(
        item_id=uuid4(),
        name=item.name,
        price=item.price,
        quantity=item.quantity,
        is_offer=item.is_offer,
        supplier=item.supplier,
        tags=item.tags,
        created_at=current_time,
        updated_at=current_time,
    )

    items.append(new_item)

    return new_item

@router.get(
    "",
    response_model=list[ItemResponse],
)
def get_items(
    search: Annotated[
        str | None,
        Query(min_length=1, max_length=50),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=settings.max_items),
    ] = 10,
    offer_only: Annotated[
        bool,
        Query(),
    ] = False,
) -> list[ItemResponse]:
    filtered_items = items

    if search is not None:
        search_results: list[ItemResponse] = []

        for item in filtered_items:
            if search.lower() in item.name.lower():
                search_results.append(item)

        filtered_items = search_results

    if offer_only is True:
        offer_results: list[ItemResponse] = []

        for item in filtered_items:
            if item.is_offer is True:
                offer_results.append(item)

        filtered_items = offer_results

    return filtered_items[:limit]

@router.get(
    "/{item_id}",
    response_model=ItemResponse,
)
def read_item(
    item_id: Annotated[UUID, Path()],
) -> ItemResponse:
    return find_item(item_id)

@router.put(
    "/{item_id}",
    response_model=ItemActionResponse,
)
def update_item(
    item_id: Annotated[UUID, Path()],
    updated_item: Item,
) -> ItemActionResponse:
    item = find_item(item_id)

    item.name = updated_item.name
    item.price = updated_item.price
    item.quantity = updated_item.quantity
    item.is_offer = updated_item.is_offer
    item.supplier = updated_item.supplier
    item.tags = updated_item.tags
    item.updated_at = datetime.now(timezone.utc)

    return ItemActionResponse(
        message="Item completely updated successfully",
        item=item,
    )

@router.patch(
    "/{item_id}",
    response_model=ItemActionResponse,
)
def partially_update_item(
    item_id: Annotated[UUID, Path()],
    updated_item: ItemUpdate,
) -> ItemActionResponse:
    item = find_item(item_id)

    for field in updated_item.model_fields_set:
        value = getattr(updated_item, field)
        setattr(item, field, value)

    item.updated_at = datetime.now(timezone.utc)

    return ItemActionResponse(
        message="Item partially updated successfully",
        item=item,
    )

@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_item(
    item_id: Annotated[UUID, Path()],
) -> Response:
    item = find_item(item_id)
    items.remove(item)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )

from fastapi import FastAPI

from app.routers.items import router as items_router
from app.settings import settings


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "message": f"Welcome to {settings.app_name}"
    }


app.include_router(items_router)

