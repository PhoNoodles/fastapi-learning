from fastapi import FastAPI

from app.routers.items import router as items_router
from app.settings import settings

from app.database import Base, engine
from app.db_models import Item

Base.metadata.create_all(bind=engine)

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