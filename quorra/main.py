from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlmodel import SQLModel

from contextlib import asynccontextmanager

import importlib.resources

from . import __version__

from .routers import onboarding
from .routers import mobile
from .routers import login_aqr
from .routers import oidc
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
app = FastAPI(title="Quorra", version=__version__, redoc_url=None, lifespan=lifespan)

# TODO: Healthcheck
# @app.get("/healthcheck")
# async def healthcheck(session: SessionDep) -> GenericResponse:
#     # Do some garbage select
#     vk.ping()
#     return GenericResponse(status="success")

# app.include_router(test.router, prefix="/test", tags=["test"])
# app.include_router(hero.router, tags=["hero"])
app.include_router(onboarding.router, prefix="/onboarding", tags=["New user onboarding"])
app.include_router(login_aqr.router, prefix="/login/aqr", tags=["Endpoints for controlling the AQR login method"])
app.include_router(mobile.router, prefix="/mobile", tags=["Mobile endpoints"])
app.include_router(oidc.router, prefix="/oidc", tags=["OIDC"])

fe_dir = importlib.resources.files("quorra") / "fe"
app.mount("/fe", StaticFiles(directory=fe_dir), name="static")

@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/fe/index.html")
