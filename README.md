# FastAPI Learning API

A backend API project built while learning professional FastAPI development practices.

## What this project demonstrates

- Typed FastAPI endpoints
- Pydantic request and response models
- SQLite database integration
- Query parameters and filtering
- Validation and error handling
- Unit and integration testing
- Automatic Swagger API documentation

## Tech stack

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- Pytest

## Running locally

```bash
git clone https://github.com/PhoNoodles/fastapi-learning.git
cd fastapi-learning

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
