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
from app.auth import get_current_user, CurrentUser, require_admin


router = APIRouter(
    prefix="/items",
    tags=["Items"],
    dependencies=[Depends(get_current_user)],
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
        owner_username=db_item.owner_username,
        tags=db_item.tags,
        created_at=db_item.created_at,
        updated_at=db_item.updated_at,
    )

def verify_item_access(db_item: ItemTable, current_user: CurrentUser) -> None:
    is_owner = (
        db_item.owner_username == current_user["username"]
    )
    is_admin = current_user["role"] == "admin"

    if not is_owner and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this item.",
        )

@router.post(
    "",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_item(item: Item,
                db: Annotated[Session, Depends(get_db)],
                current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> ItemResponse:
    db_item = ItemTable(
        name=item.name,
        price=item.price,
        quantity=item.quantity,
        is_offer=item.is_offer,
        supplier_name=item.supplier.name,
        supplier_email=item.supplier.email,
        owner_username=current_user["username"],
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
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
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
    query = db.query(ItemTable)

    if current_user["role"] != "admin":
        query = query.filter(ItemTable.owner_username == current_user["username"])

    db_items = query.all()
    filtered_items = [
        to_item_response(item)
        for item in db_items
    ]

    if search is not None:
        filtered_items = [
            item
            for item in filtered_items
            if search.lower() in item.name.lower()
        ]

    if offer_only:
        filtered_items = [
            item
            for item in filtered_items
            if item.is_offer
        ]

    return filtered_items[:limit]

@router.get(
    "/{item_id}",
    response_model=ItemResponse,
)
def read_item(
    item_id: Annotated[UUID, Path()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> ItemResponse:
    db_item = db.get(ItemTable, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found",)
    verify_item_access(db_item, current_user)
    return to_item_response(db_item)

@router.put(
    "/{item_id}",
    response_model=ItemActionResponse,
)
def update_item(
    item_id: Annotated[UUID, Path()],
    updated_item: ItemUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> ItemActionResponse:
    db_item = db.get(ItemTable, item_id)

    if db_item is None:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")

    if updated_item.supplier is not None:
        db_item.supplier_name = updated_item.supplier.name
        db_item.supplier_email = updated_item.supplier.email
    if updated_item.quantity is not None:
        db_item.quantity = updated_item.quantity
    if updated_item.is_offer is not None:
        db_item.is_offer = updated_item.is_offer
    if updated_item.tags is not None:
        db_item.tags = updated_item.tags
    db_item.updated_at = datetime.now(timezone.utc)

    return ItemActionResponse(
        message="Item completely updated successfully",
        item=to_item_response(db_item),
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
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    db_item = db.get(ItemTable, item_id)

    if db_item is None:
        raise HTTPException(
            status_code=404,
            detail=f"Item {item_id} not found",
        )

    verify_item_access(db_item, current_user)

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

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> Response:
    db_item = db.get(ItemTable, item_id)

    if db_item is None:
        raise HTTPException(
            status_code=404,
            detail=f"Item {item_id} not found",
        )
    
    verify_item_access(db_item, current_user)

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

