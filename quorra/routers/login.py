from typing import Annotated

from fastapi import APIRouter, Header
from sqlmodel import select

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

import json

from ..classes import SessionStartResponse
from ..classes import UnauthenticatedPollResponse, AuthenticatedPollResponse
from ..classes import Device
from ..classes import ErrorResponse
from ..classes import QRDataResponse, Transaction, AqrOIDCLoginTransaction
from ..classes import TransactionTypes

from ..vk_helpers import vk_session, vk_oidc_code

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
    #return SessionStartResponse(session_id=tx_id, expiration=15, qr_image=qr_image)

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


@router.get("/fepoll", responses={404: {"model": ErrorResponse}})
async def fe_poll(db_session: SessionDep, session: str) -> UnauthenticatedPollResponse | AuthenticatedPollResponse:
    """Checks the transaction state."""
    if vk.exists(vk_s):
        vk.expire(vk_s, 15)
        vk_uid: str = vk_s + ":user-id"
        vk_did: str = vk_s + ":device-id"
        if vk.exists(vk_uid):
            code: str = str(uuid4())
            vk_code: str = vk_oidc_code(code)
            await store_oidc_code(session, code)
            return AuthenticatedPollResponse(code=code, expiration=vk.expiretime(vk_code))
        elif vk.exists(vk_did):
            return UnauthenticatedPollResponse(state="identified", expiration=0)
        else:
            return UnauthenticatedPollResponse(state="waiting", expiration=vk.expiretime(vk_s))
    else:
        raise HTTPException(status_code=404, detail="Session not found")


# TODO: TBD
@router.get("/bepoll", responses={404: {"model": ErrorResponse}})
async def be_poll(db_session: SessionDep, session: str) -> None:
    return None
