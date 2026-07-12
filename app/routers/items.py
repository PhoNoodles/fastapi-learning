from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    Query,
    Response,
    status,
    Depends,
    FastAPI,
)

from sqlalchemy.orm import Session
from app.database import get_db
from app.db_models import Item as ItemTable

from app.models import (
    Item,
    ItemActionResponse,
    ItemResponse,
    ItemUpdate,
    Supplier,
)
from app.settings import settings
from app.storage import find_item, items
from app.settings import settings



router = APIRouter(
    prefix="/items",
    tags=["Items"],
)


def to_item_response(db_item: ItemTable) -> ItemResponse:
    return ItemResponse(
        item_id=db_item.item_id,
        name=db_item.name,
        price=db_item.price,
        quantity=db_item.quantity,
        is_offer=db_item.is_offer,
        supplier=Supplier(
            name=db_item.supplier_name,
            email=db_item.supplier_email,
        ),
        tags=db_item.tags,
        created_at=db_item.created_at,
        updated_at=db_item.updated_at,
    )

@router.post(
    "",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_item(item: Item,
                db: Annotated[Session, Depends(get_db)]
                ) -> ItemResponse:
    db_item = ItemTable(
        name=item.name,
        price=item.price,
        quantity=item.quantity,
        is_offer=item.is_offer,
        supplier_name=item.supplier.name,
        supplier_email=item.supplier.email,
        tags=item.tags,
    )

    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return to_item_response(db_item)

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
    db: Annotated[Session, Depends(get_db)],
) -> ItemResponse:
    db_item = db.get(ItemTable, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found",)
    return to_item_response(db_item)

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
@router.patch("/{item_id}")
def patch_item(
    item_id: UUID,
    item_update: ItemUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    db_item = db.get(ItemTable, item_id)

    if db_item is None:
        raise HTTPException(
            status_code=404,
            detail=f"Item {item_id} not found",
        )

    update_data = item_update.model_dump(
        exclude_unset=True,
    )

    for field, value in update_data.items():
        if field == "supplier":
            db_item.supplier_name = value["name"]
            db_item.supplier_email = value["email"]
        else:
            setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)

    return {
        "message": "Item updated successfully",
        "item": to_item_response(db_item),
    }
@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@router.delete("/{item_id}", status_code=204)
def delete_item(
    item_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    db_item = db.get(ItemTable, item_id)

    if db_item is None:
        raise HTTPException(
            status_code=404,
            detail=f"Item {item_id} not found",
        )

    db.delete(db_item)
    db.commit()

    return Response(status_code=204)



app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "message": f"Welcome to {settings.app_name}"
    }

