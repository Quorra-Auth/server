from typing import Annotated

from fastapi import APIRouter, Header
from sqlmodel import select

from fastapi import HTTPException

import json

from ..classes import Device
from ..classes import ErrorResponse
from ..classes import QRDataResponse, Transaction, AqrOIDCLoginTransaction
from ..classes import TransactionTypes

from ..database import SessionDep
from ..database import vk

from ..utils import generate_qr
from ..config import server_url


router = APIRouter()


@router.get("/start", status_code=201)
async def login_start(client_id: str, scope: str, nonce: str | None = None) -> Transaction:
    """Starts a new login session."""
    tx = Transaction.new("aqr-oidc-login")
    tx_id = tx.tx_id
    qr_content = "quorra+{}/mobile/login?s={}".format(server_url, tx_id)
    qr_image = generate_qr(qr_content)
    oidc_context = {"client-id": client_id, "scope": scope}
    if nonce is not None:
        oidc_context["nonce"] = nonce
    tx.add_data(".oidc_data", oidc_context)
    return tx

# TODO: Rotating login codes
@router.post("/qr", responses={404: {"model": ErrorResponse}})
def qr_gen(rq: Transaction) -> QRDataResponse:
    """Generates an AQR for the frontend"""
    tx = Transaction.load(TransactionTypes.aqr_oidc_login.value, rq.tx_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if "oidc_data" not in tx.data:
        raise HTTPException(status_code=404, detail="OIDC data is missing in transaction data")
    link = "quorra+{}/mobile/login?s={}".format(server_url, tx.tx_id)
    qr_image = generate_qr(link)
    return QRDataResponse(link=link, qr_image=qr_image)
