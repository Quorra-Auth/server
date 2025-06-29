from fastapi import APIRouter, Request, Form, Depends
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Security
from urllib.parse import urlencode
import uuid

from ..config import server_url, oidc_clients

from ..classes import ErrorResponse
from ..classes import TokenResponse

from ..vk_helpers import vk_oidc_code

from ..database import vk

from ..keys import get_jwk
from ..utils import generate_token, url_encoder


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
async def authorize(client_id: str, redirect_uri: str, state: str, nonce: str | None = None, response_type: str = "code") -> RedirectResponse:
    client = find_client(client_id)
    if client is None:
        raise HTTPException(status_code=400, detail="Invalid client")
    if redirect_uri not in client["redirect_uris"]:
        raise HTTPException(status_code=400, detail="Invalid client")
    args = {"client_id": client_id, "redirect_uri": redirect_uri, "state": state}
    if nonce is not None:
        args["nonce"] = nonce
    redirect_url = url_encoder("/fe/auth/index.html", **args)
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


@router.post("/token", responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}})
async def token(request: Request, grant_type: str = Form(...), code: str = Form(...), creds: tuple[str, str] = Depends(get_client_credentials)) -> TokenResponse:
    client_id, client_secret = creds
    vk_code: str = vk_oidc_code(code)
    if grant_type != "authorization_code" or not vk.exists(vk_code):
        raise HTTPException(status_code=400, detail="invalid_grant")
    code_context = vk.hgetall(vk_code)
    if code_context["client-id"] != client_id:
        raise HTTPException(status_code=400, detail="invalid_client")
    client = find_client(client_id)
    if client_secret != client["client_secret"]:
        raise HTTPException(status_code=401, detail="unauthorized_client")
    user: str = code_context["user-id"]
    nonce: str | None = None
    if "nonce" in code_context:
        nonce = code_context["nonce"]
    id_token = generate_token(sub=user, aud=client_id, iss=issuer, nonce=nonce)
    vk.delete(vk_code)
    # TODO: Real access-tokens
    return TokenResponse(id_token=id_token)


# TODO: Implement
@router.get("/userinfo")
def userinfo(authorization: str = ""):
    if "dummy-access-token" not in authorization:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    return {"sub": "demo_user", "name": "Demo User", "email": "demo@example.com"}
