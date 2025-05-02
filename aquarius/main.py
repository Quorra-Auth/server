from fastapi import FastAPI
from sqlmodel import SQLModel

from contextlib import asynccontextmanager

from .routers import onboarding
from .routers import test
from .routers import hero

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

# root_path="/whatever" - Make configurable
# openapi_url, docs_url - Make configurable (toggle)
# version - Pull from the project
app = FastAPI(title="Aquarius", redoc_url=None, lifespan=lifespan)

# @app.get("/healthcheck")
# async def healthcheck(session: SessionDep) -> GenericResponse:
#     # Do some garbage select
#     vk.ping()
#     return GenericResponse(status="success")

app.include_router(test.router, prefix="/test", tags=["test"])
app.include_router(hero.router, tags=["hero"])
app.include_router(onboarding.router, prefix="/onboarding", tags=["New user onboarding"])
