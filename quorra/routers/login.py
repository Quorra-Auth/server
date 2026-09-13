from typing import Annotated, Literal

from fastapi import APIRouter, Header
from sqlmodel import select

from fastapi import HTTPException

import json
import random

from ..classes import (
    Device,
    Transaction, TransactionTypes,
    ErrorResponse, QRDataResponse
)

from ..database import SessionDep
from ..database import vk

from ..config import server_url
from .oidc import find_client

router = APIRouter()


@router.get("/start", status_code=201)
async def login_start(client_id: str, scope: str, nonce: str | None = None, code_challenge: str | None = None, code_challenge_method: Literal["S256"] | None = None) -> Transaction:
    """Starts a new login session."""
    if "openid" not in scope:
        raise HTTPException(status_code=400, detail="The 'openid' scope is always required")
    client = find_client(client_id)
    if client is None:
        raise HTTPException(status_code=400, detail="Invalid client")
    tx = Transaction.new("ln-oidc-login")
    k1 = random.randbytes(32).hex()
    tx.add_data(".ln", {"k1": k1})
    oidc_context = {"client-id": client_id, "scope": scope}
    if nonce is not None:
        oidc_context["nonce"] = nonce
    if code_challenge_method is not None:
        oidc_context["code_challenge_method"] = code_challenge_method
    if code_challenge is not None:
        oidc_context["code_challenge"] = code_challenge
    tx.add_data(".oidc_data", oidc_context)
    return tx

