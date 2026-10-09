from os import O_LARGEFILE

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer, SecurityScopes
from typing import Annotated
from .classes import (
    LnOIDCLoginTransaction
)
from .config import server_url

issuer = server_url + "/oidc"

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{issuer}/authorize",
    tokenUrl=f"{issuer}/token",
    scopes={
        "openid": "Always required",
        "profile": "Basic profile info",
        "email": "email"
    }
)

def oidc_auth(security_scopes: SecurityScopes, access_token: str = Depends(oauth2_scheme)):
    tx = LnOIDCLoginTransaction.find_by("oidc_at", access_token)
    if tx is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    user = tx._private_data["user"]["uid"]
    client_id = tx.data["oidc_data"]["client-id"]
    token_scopes = tx.data["oidc_data"]["scope"].split()
    for required in security_scopes.scopes:
        if required not in token_scopes:
            raise HTTPException(status_code=403, detail="insufficient_scope", headers={"WWW-Authenticate": f'Bearer scope="{security_scopes.scope_str}"'})
    claims = {"sub": user, "aud": client_id, "iss": issuer, "scope": tx.data["oidc_data"]["scope"]}
    return claims
