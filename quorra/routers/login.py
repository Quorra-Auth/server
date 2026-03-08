from typing import Annotated

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


router = APIRouter()


@router.get("/start", status_code=201)
async def login_start(client_id: str, scope: str, nonce: str | None = None) -> Transaction:
    """Starts a new login session."""
    tx = Transaction.new("ln-oidc-login")
    tx_id = tx.tx_id
    k1 = random.randbytes(32).hex()
    tx.add_data(".ln", {"k1": k1})
    oidc_context = {"client-id": client_id, "scope": scope}
    if nonce is not None:
        oidc_context["nonce"] = nonce
    tx.add_data(".oidc_data", oidc_context)
    return tx

