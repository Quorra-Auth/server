from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlmodel import SQLModel, select

from contextlib import asynccontextmanager

import importlib.resources

from . import __version__

from .routers import onboarding
from .routers import mobile
from .routers import login
from .routers import login_aqr
from .routers import oidc

from .database import engine
from .database import SessionDep
from .database import vk

async def migrate():
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Running migrations")
    await migrate()
    yield
    print("Main lifespan done")

# TODO: root_path="/whatever" - Make configurable
# TODO: openapi_url, docs_url - Make configurable (toggle)
app = FastAPI(title="Quorra", version=__version__, redoc_url=None, lifespan=lifespan)


@app.get("/health", include_in_schema=False)
async def healthcheck(session: SessionDep):
    # Do some garbage select
    session.exec(select(1)).first()
    vk.ping()
    return {"health": "ok"}


app.include_router(onboarding.router, prefix="/onboarding", tags=["New user onboarding"])
app.include_router(login.router, prefix="/login", tags=["Login session management"])
app.include_router(login_aqr.router, prefix="/login/aqr", tags=["Endpoints for controlling the AQR login method"])
app.include_router(mobile.router, prefix="/mobile", tags=["Mobile endpoints"])
app.include_router(oidc.router, prefix="/oidc", tags=["OIDC"])

fe_dir = importlib.resources.files("quorra") / "fe"
app.mount("/fe", StaticFiles(directory=fe_dir), name="static")

@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/fe/onboard/index.html")
