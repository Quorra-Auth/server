from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlmodel import select

from contextlib import asynccontextmanager

import importlib.resources

from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command

from . import __version__

from .routers import (
    onboarding, login,
    lnurlauth, oidc, tx
)

from .database import engine, SessionDep, vk
from .config import config as quorra_config

from .valkey_indexes import ensure_indexes_with_retry

def migrate():
    with vk.lock("quorra:migration-lock", timeout=300, blocking_timeout=300):
        run_alembic_upgrade()

def run_alembic_upgrade():
    migrations_dir = importlib.resources.files("quorra") / "migrations"
    alembic_cfg = AlembicConfig()
    alembic_cfg.set_main_option("script_location", str(migrations_dir))
    alembic_cfg.set_main_option("sqlalchemy.url", quorra_config["database"]["sql"]["string"])
    alembic_command.upgrade(alembic_cfg, "head")

def prep_valkey():
    # TODO: Error handling and a friendly message when missing JSON/Search modules
    print("Ensuring Valkey indexes...")
    ensure_indexes_with_retry()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Running migrations")
    prep_valkey()
    migrate()
    yield
    print("Main lifespan done")

# TODO: root_path="/whatever" - Make configurable
# TODO: openapi_url, docs_url - Make configurable (toggle)
app = FastAPI(title="Quorra", version=__version__, redoc_url=None, lifespan=lifespan)


@app.get("/health", include_in_schema=False)
def healthcheck(session: SessionDep):
    # Do some garbage select
    session.exec(select(1)).first()
    vk.ping()
    return {"health": "ok"}


app.include_router(onboarding.router, prefix="/processes/onboarding", tags=["Onboarding process endpoints"])
app.include_router(login.router, prefix="/processes/login", tags=["Login process endpoints"])
app.include_router(lnurlauth.router, prefix="/lnurl-auth", tags=["Lightning login endpoints"])
app.include_router(oidc.router, prefix="/oidc", tags=["OIDC"])
app.include_router(tx.router, prefix="/tx", tags=["Transaction management"])

fe_dir = importlib.resources.files("quorra") / "fe"
app.mount("/fe", StaticFiles(directory=fe_dir, html=True), name="static")

@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/fe/onboard/")
