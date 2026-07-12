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