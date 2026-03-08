from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlmodel import SQLModel, select

from contextlib import asynccontextmanager

import importlib.resources

from . import __version__

from .routers import (
    onboarding, login,
    lnurlauth, oidc, tx
)

from .database import engine, SessionDep, vk

from valkey.exceptions import ResponseError
from valkey.commands.search.field import TagField
from valkey.commands.search.indexDefinition import IndexDefinition, IndexType

async def migrate():
    SQLModel.metadata.create_all(engine)

async def prep_valkey():
    # TODO: Make it a loop over a dict of indexes and schemas
    # TODO: Error handling and a friendly message when missing JSON/Search modules
    print("Creating indexes in Valkey...")
    await create_drt_index()
    await create_oidc_code_index()
    await create_oidc_at_index()

async def create_drt_index():
    idx = vk.ft("idx:ln_k1")
    schema = (TagField("$.data.ln.k1", as_name="ln_k1"))
    try:
        idx.info()
    except ResponseError:
        idx.create_index(
            schema,
            definition=IndexDefinition(
                prefix=["ln-oidc-login:", "onboarding:"],
                index_type=IndexType.JSON
            )
        )
    info = idx.info()
    print("{} - {} documents, attributes: {}".format(info["index_name"], info["num_docs"], info["attributes"]))

async def create_oidc_code_index():
    idx = vk.ft("idx:oidc_code")
    schema = (TagField("$.data.oidc_data.code", as_name="oidc_code"))
    try:
        idx.info()
    except ResponseError:
        idx.create_index(
            schema,
            definition=IndexDefinition(
                prefix=["ln-oidc-login:"],
                index_type=IndexType.JSON
            )
        )
    info = idx.info()
    print("{} - {} documents, attributes: {}".format(info["index_name"], info["num_docs"], info["attributes"]))

async def create_oidc_at_index():
    idx = vk.ft("idx:oidc_at")
    schema = (TagField("$.private.oidc_data.access_token", as_name="oidc_at"))
    try:
        idx.info()
    except ResponseError:
        idx.create_index(
            schema,
            definition=IndexDefinition(
                prefix=["ln-oidc-login:"],
                index_type=IndexType.JSON
            )
        )
    info = idx.info()
    print("{} - {} documents, attributes: {}".format(info["index_name"], info["num_docs"], info["attributes"]))

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Running migrations")
    await migrate()
    await prep_valkey()
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
