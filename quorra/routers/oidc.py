from fastapi import APIRouter, Request, Form
from fastapi import HTTPException
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from urllib.parse import urlencode
import uuid

from ..config import server_url, oidc_clients

from ..vk_helpers import vk_oidc_code

from ..database import vk

from ..keys import get_jwk
from ..utils import generate_token, url_encoder

# TODO: This whole file needs type annotations, proper responses, etc.
router = APIRouter()
issuer = server_url + "/oidc"


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


@router.get("/authorize")
def authorize(client_id: str, redirect_uri: str, state: str, nonce: str | None = None, response_type: str = "code"):
    for client in oidc_clients:
        if client_id == client["client_id"]:
            if redirect_uri not in client["redirect_uris"]:
                raise HTTPException(status_code=400, detail="Invalid client")
        else:
            raise HTTPException(status_code=400, detail="Invalid client")
    args = {"client_id": client_id, "redirect_uri": redirect_uri, "state": state}
    if nonce is not None:
        args["nonce"] = nonce
    redirect_url = url_encoder("/fe/index.html", **args)
    return RedirectResponse(url=redirect_url)


@router.post("/token")
async def token(grant_type: str = Form(...), code: str = Form(...), client_id: str = Form(...)):
    vk_code: str = vk_oidc_code(code)
    if grant_type != "authorization_code" or not vk.exists(vk_code):
        return JSONResponse({"error": "invalid_grant"}, status_code=400)
    code_context = vk.hgetall(vk_code)
    if code_context["client-id"] != client_id:
        return JSONResponse({"error": "invalid_client"}, status_code=400)
    user: str = code_context["user-id"]
    nonce: str | None = None
    if "nonce" in code_context:
        nonce = code_context["nonce"]
    id_token = generate_token(sub=user, aud=client_id, iss=issuer, nonce=nonce)
    vk.delete(vk_code)
    # TODO: Real access-tokens
    return {
        "access_token": "dummy-access-token",
        "token_type": "Bearer",
        "id_token": id_token
    }


# TODO: Implement
@router.get("/userinfo")
def userinfo(authorization: str = ""):
    if "dummy-access-token" not in authorization:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    return {"sub": "demo_user", "name": "Demo User", "email": "demo@example.com"}
