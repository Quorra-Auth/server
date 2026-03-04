from fastapi import APIRouter, Request, Form, Depends, Header
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Security
from urllib.parse import urlencode
from sqlmodel import select
from uuid import uuid4
from typing import Annotated

from ..config import server_url, oidc_clients

from ..classes import (
    User, Transaction,
    TokenResponse, ErrorResponse
)

from valkey.commands.search.query import Query

from ..database import SessionDep
from ..database import vk

from ..keys import get_jwk
from ..utils import generate_token, url_encoder, escape_valkey_tag


security_scheme = HTTPBasic(auto_error=False)
router = APIRouter()
issuer = server_url + "/oidc"


def find_client(client_id: str) -> dict | None:
    for client in oidc_clients:
        if client_id == client["client_id"]:
            return client
    return None


@router.get("/.well-known/openid-configuration")
def config():
    return {
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/authorize",
        "token_endpoint": f"{issuer}/token",
        "userinfo_endpoint": f"{issuer}/userinfo",
        "jwks_uri": f"{issuer}/.well-known/jwks.json",
        "response_types_supported": ["code"],
        "id_token_signing_alg_values_supported": ["RS256"]
    }


@router.get("/.well-known/jwks.json")
def jwks():
    return {"keys": [get_jwk()]}


@router.get("/authorize", status_code=307, responses={400: {"model": ErrorResponse}})
async def authorize(client_id: str, redirect_uri: str, state: str, scope: str, nonce: str | None = None, response_type: str = "code") -> RedirectResponse:
    client = find_client(client_id)
    if client is None:
        raise HTTPException(status_code=400, detail="Invalid client")
    if redirect_uri not in client["redirect_uris"]:
        raise HTTPException(status_code=400, detail="Invalid client")
    args = {"client_id": client_id, "redirect_uri": redirect_uri, "state": state, "scope": scope}
    if nonce is not None:
        args["nonce"] = nonce
    redirect_url = url_encoder("/fe/auth/", **args)
    return RedirectResponse(url=redirect_url)


def get_client_credentials(
    request: Request,
    form_client_id: str = Form(None),
    form_client_secret: str = Form(None),
    basic_creds: HTTPBasicCredentials = Security(security_scheme)
):
    # Prefer HTTP Basic
    if basic_creds and basic_creds.username and basic_creds.password:
        return basic_creds.username, basic_creds.password

    # Fallback to form
    return form_client_id, form_client_secret


async def store_oidc_code(tx: Transaction):
    code: str = str(uuid4())
    tx.add_data(".oidc_data.code", code)


@router.post("/token", responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}})
async def token(db_session: SessionDep, request: Request, grant_type: str = Form(...), code: str = Form(...), creds: tuple[str, str] = Depends(get_client_credentials)) -> TokenResponse:
    # Other grants are not supported
    if grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="invalid_grant")
    client_id, client_secret = creds
    # Look up the transaction if initial checks pass
    safe_code = escape_valkey_tag(code)
    q = Query(f"@oidc_code:{{{safe_code}}}")
    res = vk.ft("idx:oidc_code").search(q)
    if res.total == 1:
        tx_id = res.docs[0]["id"].split(":")[-1]
        tx = Transaction.load("ln-oidc-login", tx_id)
    else:
        raise HTTPException(status_code=400, detail="invalid_grant")
    # Final checks before issuing the ID token
    client = find_client(client_id)
    if tx.data["oidc_data"]["client-id"] != client_id:
        raise HTTPException(status_code=400, detail="invalid_client")
    elif client_secret != client["client_secret"]:
        raise HTTPException(status_code=401, detail="unauthorized_client")
    user: str = tx._private_data["user"]["uid"]
    token_claims = {"sub": user, "aud": client_id, "iss": issuer}
    if "nonce" in tx.data["oidc_data"]:
        token_claims["nonce"] = tx.data["oidc_data"]["nonce"]
    if "profile" in tx.data["oidc_data"]["scope"]:
        username = db_session.exec(select(User.username).where(User.id == user)).one()
        token_claims["nickname"] = username
    if "email" in tx.data["oidc_data"]["scope"]:
        email = db_session.exec(select(User.email).where(User.id == user)).one()
        token_claims["email"] = email
    id_token = generate_token(token_claims)
    access_token = str(uuid4())
    tx.add_private_data(".oidc_data", {"access_token": access_token})
    tx.set_state("token-issued")
    # TODO: Real access-tokens
    return TokenResponse(id_token=id_token, access_token=access_token)


# TODO: Implement checking scopes
@router.get("/userinfo", responses={401: {"model": ErrorResponse}})
def userinfo(authorization: Annotated[str | None, Header(alias="Authorization")] = None):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="unauthorized")
    access_token = authorization.removeprefix("Bearer ")
    safe_auth = escape_valkey_tag(access_token)
    q = Query(f"@oidc_at:{{{safe_auth}}}")
    res = vk.ft("idx:oidc_at").search(q)
    if res.total == 1:
        tx_id = res.docs[0]["id"].split(":")[-1]
        tx = Transaction.load("ln-oidc-login", tx_id)
    else:
        raise HTTPException(status_code=401, detail="unauthorized")
    user = tx._private_data["user"]["uid"]
    client_id = tx.data["oidc_data"]["client-id"]
    claims = {"sub": user, "aud": client_id, "iss": issuer}
    return claims
