from fastapi import FastAPI
from sqlmodel import SQLModel

from contextlib import asynccontextmanager

from .routers import onboarding
from .routers import mobile
from .routers import login_aqr
# from .routers import test
# from .routers import hero

from .database import engine

async def migrate():
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Running migrations")
    #print("Main lifespan done")
    await migrate()
    yield
    print("Main lifespan done")

# TODO: root_path="/whatever" - Make configurable
# TODO: openapi_url, docs_url - Make configurable (toggle)
# TODO: version - Pull from the project
app = FastAPI(title="Quorra", redoc_url=None, lifespan=lifespan)

# TODO: Healthcheck
# @app.get("/healthcheck")
# async def healthcheck(session: SessionDep) -> GenericResponse:
#     # Do some garbage select
#     vk.ping()
#     return GenericResponse(status="success")

# app.include_router(test.router, prefix="/test", tags=["test"])
# app.include_router(hero.router, tags=["hero"])
app.include_router(onboarding.router, prefix="/onboarding", tags=["New user onboarding"])
app.include_router(mobile.router, prefix="/mobile", tags=["Mobile endpoints"])
app.include_router(login_aqr.router, prefix="/login/aqr", tags=["Endpoints for controlling the AQR login method"])
