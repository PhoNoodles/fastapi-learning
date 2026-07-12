from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_read_root() -> None:
    response = client.get("/")

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
    )

    assert create_response.status_code == 201

    created_item = create_response.json()
    item_id = created_item["item_id"]

    get_response = client.get(f"/items/{item_id}")

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
    )

    assert create_response.status_code == 201

    item_id = create_response.json()["item_id"]

    delete_response = client.delete(f"/items/{item_id}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = client.get(f"/items/{item_id}")

    assert get_response.status_code == 404
    assert get_response.json() == {
        "detail": f"Item {item_id} not found"
    }