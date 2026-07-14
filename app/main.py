import time
from uuid import uuid4 

from fastapi import FastAPI, Request

from app.routers.items import router as items_router
from app.settings import settings

from app.database import Base, engine
from app.db_models import Item



Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

@app.middleware("http")
async def log_request(request: Request, call_next):

    print("1. log_requests before")
    response = await call_next(request)
    print("1. log_requests after")
    
    return response

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):

    start_time = time.perf_counter()
    print("2. add_process_time_header before")
    response = await call_next(request)
    print("2. add_process_time_header after")
    duration = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(duration)

    return response

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    print("3. add_request_id before")
    request_id = str(uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    print("3. add_request_id after")
    return response




@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "message": f"Welcome to {settings.app_name}"
    }


app.include_router(items_router)