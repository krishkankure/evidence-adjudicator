import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers.adjudications import router as adjudication_router
from app.api.routers.claims import router as claims_router
from app.api.routers.health import router as health_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.schemas.errors import ErrorBody, ErrorResponse

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized")




@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0] if exc.errors() else {}
    msg = first.get("msg", "Invalid input")
    body = ErrorResponse(error=ErrorBody(code="bad_request", message=msg)).model_dump()
    return JSONResponse(status_code=400, content=body)

@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    body = ErrorResponse(error=ErrorBody(code=exc.code, message=exc.message)).model_dump()
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(Exception)
async def generic_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    body = ErrorResponse(error=ErrorBody(code="internal_error", message="Unexpected server error")).model_dump()
    return JSONResponse(status_code=500, content=body)


app.include_router(health_router)
app.include_router(claims_router)
app.include_router(adjudication_router)
