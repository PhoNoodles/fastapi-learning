import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from collections.abc import Generator

from app.database import Base, get_db
from app.main import app
from app.settings import settings

USER_HEADERS = {
    "Authorization": "Bearer secret-token"
}

ADMIN_HEADERS = {
    "Authorization": "Bearer admin-token"
}

DATABASE_URL = "sqlite:///:memory:"


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


client = TestClient(app)



@pytest.fixture(autouse=True)
def setup_database() -> Generator[None, None, None]:
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)

def test_items_start_empty() -> None:
    response = client.get("/items", headers=USER_HEADERS)

    assert response.status_code == 200
    assert response.json() == []


def test_read_root() -> None:
    response = client.get("/", headers=USER_HEADERS)

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to FastAPI Learning API"
    }


def test_create_item() -> None:
    response = client.post(
        "/items",
        json={
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
        },
        headers=USER_HEADERS,
    )

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["name"] == "Gaming Keyboard"
    assert response_data["price"] == 89.99
    assert response_data["quantity"] == 5
    assert response_data["is_offer"] is True

def test_create_item_with_negative_price() -> None:
    response = client.post(
        "/items",
        json={
            "name": "Keyboard",
            "price": -10,
            "quantity": 5,
            "is_offer": False,
            "supplier": {
                "name": "Tech Supply Co.",
                "email": "sales@techsupply.com",
            },
            "tags": [],
        },
        headers=USER_HEADERS,
    )

    assert response.status_code == 422

def test_offer_requires_tag() -> None:
    response = client.post(
        "/items",
        json={
            "name": "Keyboard",
            "price": 49.99,
            "quantity": 5,
            "is_offer": True,
            "supplier": {
                "name": "Tech Supply Co.",
                "email": "sales@techsupply.com",
            },
            "tags": [],
        },
        headers=USER_HEADERS,
    )

    assert response.status_code == 422

def test_read_created_item() -> None:
    create_response = client.post(
        "/items",
        json={
            "name": "Mechanical Keyboard",
            "price": 109.99,
            "quantity": 3,
            "is_offer": False,
            "supplier": {
                "name": "Tech Supply Co.",
                "email": "sales@techsupply.com",
            },
            "tags": ["keyboard"],
        },
        headers=USER_HEADERS,
    )

    assert create_response.status_code == 201

    created_item = create_response.json()
    item_id = created_item["item_id"]

    get_response = client.get(f"/items/{item_id}", headers=USER_HEADERS)

    assert get_response.status_code == 200
    assert get_response.json()["item_id"] == item_id
    assert get_response.json()["name"] == "Mechanical Keyboard"

def test_patch_item() -> None:
    create_response = client.post(
        "/items",
        json={
            "name": "Office Keyboard",
            "price": 79.99,
            "quantity": 4,
            "is_offer": False,
            "supplier": {
                "name": "Tech Supply Co.",
                "email": "sales@techsupply.com",
            },
            "tags": ["office"],
        },
        headers=USER_HEADERS,
    )

    assert create_response.status_code == 201

    created_item = create_response.json()
    item_id = created_item["item_id"]
    original_created_at = created_item["created_at"]
    original_updated_at = created_item["updated_at"]

    patch_response = client.patch(
        f"/items/{item_id}",
        json={
            "price": 69.99,
            "quantity": 7,
        },
        headers=USER_HEADERS,
    )

    assert patch_response.status_code == 200

    response_data = patch_response.json()
    updated_item = response_data["item"]

    assert updated_item["price"] == 69.99
    assert updated_item["quantity"] == 7

    assert updated_item["name"] == "Office Keyboard"
    assert updated_item["supplier"]["name"] == "Tech Supply Co."
    assert updated_item["tags"] == ["office"]

    assert updated_item["created_at"] == original_created_at
    assert updated_item["updated_at"] != original_updated_at

def test_delete_item() -> None:
    create_response = client.post(
        "/items",
        json={
            "name": "Temporary Keyboard",
            "price": 39.99,
            "quantity": 2,
            "is_offer": False,
            "supplier": {
                "name": "Tech Supply Co.",
                "email": "sales@techsupply.com",
            },
            "tags": ["temporary"],
        },
        headers=USER_HEADERS,
    )

    assert create_response.status_code == 201

    item_id = create_response.json()["item_id"]

    delete_response = client.delete(f"/items/{item_id}", headers=ADMIN_HEADERS)

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = client.get(f"/items/{item_id}", headers=USER_HEADERS)

    assert get_response.status_code == 404
    assert get_response.json() == {
        "detail": f"Item {item_id} not found"
    }

def test_read_missing_item() -> None:
    missing_id = "550e8400-e29b-41d4-a716-446655440000"

    response = client.get(f"/items/{missing_id}", headers=USER_HEADERS)

    assert response.status_code == 404
    assert response.json() == {
        "detail": f"Item {missing_id} not found"
    }

def test_reject_invalid_uuid() -> None:
    response = client.get("/items/not-a-valid-uuid", headers=USER_HEADERS)

    assert response.status_code == 422

def test_get_items_requires_authentication() -> None:
    response = client.get("/items")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or missing token"
    }

def test_regular_user_cannot_delete_item() -> None:
    create_response = client.post(
        "/items",
        json={
            "name": "Protected Keyboard",
            "price": 59.99,
            "quantity": 3,
            "is_offer": False,
            "supplier": {
                "name": "Tech Supply Co.",
                "email": "sales@techsupply.com",
            },
        },
        headers=USER_HEADERS,
    )

    assert create_response.status_code == 201

    item_id = create_response.json()["item_id"]

    delete_response = client.delete(f"/items/{item_id}", headers=USER_HEADERS)

    assert delete_response.status_code == 403
    assert delete_response.json() == {
        "detail": "Admin privileges required"
    }

def test_admin_can_delete_item() -> None:
    create_response = client.post(
        "/items",
        json={
            "name": "Admin Keyboard",
            "price": 99.99,
            "quantity": 5,
            "is_offer": False,
            "supplier": {
                "name": "Tech Supply Co.",
                "email": "sales@techsupply.com",
            },
        },
        headers=ADMIN_HEADERS,
    )

    assert create_response.status_code == 201

    item_id = create_response.json()["item_id"]

    delete_response = client.delete(f"/items/{item_id}", headers=ADMIN_HEADERS)

    assert delete_response.status_code == 204
    assert delete_response.content == b""