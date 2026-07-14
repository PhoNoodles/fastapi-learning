from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


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
                    "tags": ["gaming", "keyboard"],
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

    @model_validator(mode="after")
    def validate_offer(self):
        if self.is_offer is True and len(self.tags) == 0:
            raise ValueError(
                "Offer items must have at least one tag"
            )

        return self


class ItemUpdate(BaseModel):
    name: Annotated[
        str | None,
        Field(min_length=2, max_length=50),
    ] = None

    price: Annotated[
        float | None,
        Field(gt=0),
    ] = None

    quantity: Annotated[
        int | None,
        Field(ge=1, le=100),
    ] = None

    is_offer: bool | None = None
    supplier: Supplier | None = None

    tags: Annotated[
        list[str] | None,
        Field(max_length=5),
    ] = None

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
    owner_username: str
    created_at: datetime
    updated_at: datetime


class ItemActionResponse(BaseModel):
    message: str
    item: ItemResponse