from fastapi import FastAPI, HTTPException, Path, Query, Response, status
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Annotated
from datetime import datetime, timezone
from uuid import UUID, uuid4

def clean_tags(tags: list[str]) -> list[str]:
    cleaned_tags: list[str] = []

    for tag in tags:
        cleaned_tag = tag.strip().lower()

        if len(cleaned_tag) < 2:
            raise ValueError(
                "Each tag must contain at least 2 characters"
            )

        if cleaned_tag not in cleaned_tags:
            cleaned_tags.append(cleaned_tag)

    return cleaned_tags


app = FastAPI()

class Supplier(BaseModel):
    name: Annotated[
        str,
        Field(min_length=2, max_length=100),
    ]

    email: Annotated[
        str,
        Field(min_length=5, max_length=100),
    ]

class Item(BaseModel):

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Gaming Keyboard",
                    "price": 89.99,
                    "quantity": 5,
                    "is_offer": True,
                    "supplier": {
                        "name": "Tech Supply Co.",
                        "email": "sales@techsupply.com",
                    },
                    "tags": [
                        "gaming",
                        "keyboard",
                    ],
                }
            ]
        }
    )

    name: Annotated[
        str,
        Field(min_length=2, max_length=50),
    ]

    price: Annotated[
        float,
        Field(gt=0),
    ]

    quantity: Annotated[
        int,
        Field(ge=1, le=100),
    ]

    is_offer: bool | None = None
    supplier: Supplier
    tags: Annotated[
        list[str],
        Field(max_length=5),
    ] = Field(default_factory=list)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags: list[str]) -> list[str]:
        return clean_tags(tags)
    
    @model_validator(mode="before")
    @classmethod
    def clean_raw_name(
        cls,
        data: dict[str, object],
    ) -> dict[str, object]:
        data = data.copy()

        name = data.get("name")

        if isinstance(name, str):
            data["name"] = name.strip()

        return data
    
    @model_validator(mode="after")
    def validate_offer(self):
        if self.is_offer is True and len(self.tags) == 0:
            raise ValueError(
                "Offer items must have at least one tag"
            )

        return self

class ItemUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "price": 69.99,
                    "quantity": 8,
                    "tags": [
                        "sale",
                        "keyboard",
                    ],
                }
            ]
        }
    )

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
    )

    price: float | None = Field(
        default=None,
        gt=0,
    )

    quantity: int | None = Field(
        default=None,
        ge=1,
        le=100,
    )

    is_offer: bool | None = None
    supplier: Supplier | None = None
    tags: list[str] | None = None
    @field_validator("tags")
    @classmethod
    def validate_tags(
        cls,
        tags: list[str] | None,
    ) -> list[str] | None:
        if tags is None:
            return None

        return clean_tags(tags)

class ItemResponse(BaseModel):
    item_id: UUID
    name: str
    price: float
    quantity: int
    is_offer: bool | None = None
    supplier: Supplier
    tags: list[str]
    created_at: datetime
    updated_at: datetime

class ItemActionResponse(BaseModel):
    message: str
    item: ItemResponse


items: list[ItemResponse] = []

def find_item_by_id(item_id: Annotated[UUID, Path(description="The ID of the item")]) -> ItemResponse:
    for item in items:
        if item.item_id == item_id:
            return item
    raise HTTPException(status_code=404, detail=f"Item {item_id} not found")

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: Annotated[UUID, Path(description="The ID of the item")]):
    return find_item_by_id(item_id)

@app.put("/items/{item_id}", response_model=ItemActionResponse )
def update_item(
    item_id: Annotated[UUID, Path(description="The ID of the item")],
    updated_item: ItemUpdate,
) -> ItemActionResponse:
    item = find_item_by_id(item_id)

    if updated_item.name is not None:
        item.name = updated_item.name
    if updated_item.price is not None:
        item.price = updated_item.price
    if updated_item.quantity is not None:
        item.quantity = updated_item.quantity
    if updated_item.is_offer is not None:
        item.is_offer = updated_item.is_offer
    if updated_item.supplier is not None:
        item.supplier = updated_item.supplier
    if updated_item.tags is not None:
        item.tags = updated_item.tags
    item.updated_at = datetime.now(timezone.utc)

    return ItemActionResponse(
        message="Item updated successfully",
        item=item,
    )

@app.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item: Item):
    new_item = ItemResponse(
        item_id=uuid4(),
        name=item.name,
        price=item.price,
        quantity=item.quantity,
        is_offer=item.is_offer,
        supplier=item.supplier,
        tags=item.tags,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    items.append(new_item)

    return new_item

@app.get("/items", response_model=list[ItemResponse])
def get_items(
    search: Annotated[
        str | None, 
        Query(min_length=1, max_length=50, 
              description="Search for items by name")
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=100, 
              description="Limit the number of items returned"),
    ] = 10,
    offer_only: Annotated[
        bool,
        Query(
            description="Filter items based on whether they are on offer or not",
        ),
    ] = False,
):
    filtered_items = items 

    if search is not None:
        search_results: list[ItemResponse] = []
        for item in items:
            if search.lower() in item.name.lower():
                search_results.append(item)

        filtered_items = search_results

    if offer_only is True:
        offer_items: list[ItemResponse] = []

        for item in filtered_items:
            if item.is_offer is True:
                offer_items.append(item)
        filtered_items = offer_items

    return filtered_items[:limit]

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: Annotated[UUID, Path(description="The ID of the item")]):
    item = find_item_by_id(item_id)

    items.remove(item)

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.patch("/items/{item_id}", response_model=ItemActionResponse)
def partially_update_item(
    item_id: Annotated[UUID, Path(description="The ID of the item")],
    updated_item: ItemUpdate,
) -> ItemActionResponse:
    item = find_item_by_id(item_id)

    for field in updated_item.model_fields_set:
        value = getattr(updated_item, field)
        setattr(item, field, value)

    item.updated_at = datetime.now(timezone.utc)

    return ItemActionResponse(
        message="Item partially updated successfully",
        item=item,
    )