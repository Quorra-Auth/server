from os import O_LARGEFILE

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer, SecurityScopes
from typing import Annotated
from valkey.commands.search.query import Query
from .utils import escape_valkey_tag
from .database import vk
from .classes import (
    Transaction
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
    safe_auth = escape_valkey_tag(access_token)
    q = Query(f"@oidc_at:{{{safe_auth}}}")
    res = vk.ft("idx:oidc_at").search(q)
    if res.total == 1:
        tx_id = res.docs[0]["id"].split(":")[-1]
        tx = Transaction.load("ln-oidc-login", tx_id)
        if tx is None:
            raise HTTPException(status_code=500, detail="fuck")
    else:
        raise HTTPException(status_code=401, detail="unauthorized")
    user = tx._private_data["user"]["uid"]
    client_id = tx.data["oidc_data"]["client-id"]
    token_scopes = tx.data["oidc_data"]["scope"].split()
    for required in security_scopes.scopes:
        if required not in token_scopes:
            raise HTTPException(status_code=403, detail="insufficient_scope", headers={"WWW-Authenticate": f'Bearer scope="{security_scopes.scope_str}"'})
    claims = {"sub": user, "aud": client_id, "iss": issuer, "scope": tx.data["oidc_data"]["scope"]}
    return claims
