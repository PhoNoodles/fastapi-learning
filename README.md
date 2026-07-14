# FastAPI Learning API

A learning project built with FastAPI, SQLAlchemy, SQLite, pytest, authentication, and authorization.

## Features

- FastAPI CRUD routes
- Pydantic request and response validation
- SQLAlchemy ORM
- SQLite persistence
- Isolated pytest database tests
- Request logging middleware
- Process-time response headers
- Request ID middleware
- Bearer-token authentication
- Role-based authorization
- Ownership-based authorization
- Admin access across users

## Authorization Rules

- Regular users can view only their own items
- Owners can read, update, and delete their own items
- Non-owners receive `403 Forbidden`
- Admins can access all items

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
fastapi dev app/main.py