from typing import Annotated

from fastapi import APIRouter, Header
from sqlmodel import select

from fastapi import HTTPException

from uuid import uuid4
import json
import base64
import bech32
import random

from sqlalchemy.exc import IntegrityError

from ..classes import (
    User, Device,
    Transaction, TransactionTypes,
    ErrorResponse, QRDataResponse
)

from cryptography.hazmat.primitives.asymmetric.ec import (
    ECDSA,
    SECP256K1,
    EllipticCurvePublicKey,
)
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature, Prehashed
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.exceptions import InvalidSignature

from valkey.commands.search.query import Query

from .oidc import store_oidc_code

from ..database import SessionDep
from ..database import vk

from ..utils import generate_qr
from ..utils import escape_valkey_tag
from ..utils import generate_qr
from ..config import server_url

router = APIRouter()

async def verify_signature(k1: str, sig: str, key: str) -> bool:
    pubkey_bytes = bytes.fromhex(key)
    pubkey = EllipticCurvePublicKey.from_encoded_point(SECP256K1(), pubkey_bytes)
    k1_bytes = bytes.fromhex(k1)
    signature_bytes = bytes.fromhex(sig)
    try:
        pubkey.verify(signature_bytes, k1_bytes, ECDSA(Prehashed(hashes.SHA256())))
    except InvalidSignature:
        return False
    return True


@router.get("/register", response_model=None, responses={403: {"model": ErrorResponse}})
async def ln_register(session: SessionDep, k1: str, tag: str, sig: str, key: str, action: str | None = None):
    """Finishes device registration."""
    if not await verify_signature(k1, sig, key):
        raise HTTPException(status_code=403, detail="Invalid signature")
    safe_k1 = escape_valkey_tag(k1)
    q = Query(f"@ln_k1:{{{safe_k1}}}")
    res = vk.ft("idx:ln_k1").search(q)
    if res.total == 1:
        tx_id = res.docs[0]["id"].split(":")[-1]
        tx = Transaction.load(TransactionTypes.onboarding.value, tx_id)
        # OPTION 1 - new user registration - transaction data contains the entry object
        if "entry" in tx._private_data:
            user_details = tx._private_data["entry"]
            u: User = User(id=str(uuid4()), username=user_details["username"], email=user_details["email"])
            session.add(u)
            session.commit()
            session.refresh(u)
            uid: int = u.id
    # TODO: OPTION 2 - user exists, only register device - the transaction should contain an existing user ID
    else:
        raise HTTPException(status_code=403, detail="Token invalid")
    d: Device = Device(pubkey=key, user_id=uid, id=str(uuid4()))
    session.add(d)
    try:
        session.commit()
    except IntegrityError:
        # TODO: Proper status code
        raise HTTPException(status_code=403, detail="This public key already exists in a different device")
    session.refresh(d)
    # TODO: Pass the error back into the transaction if anything fails
    tx.set_state("finished")
    return None


# TODO: Implement for LN
# @router.post("/aqr/identify", response_model=None, responses={403: {"model": ErrorResponse}})
# async def aqr_identify(db_session: SessionDep):
#     return None


@router.get("/authenticate", response_model=None, responses={404: {"model": ErrorResponse}})
async def ln_authenticate(session: SessionDep, k1: str, tag: str, sig: str, key: str, action: str | None = None):
    if not await verify_signature(k1, sig, key):
        raise HTTPException(status_code=403, detail="Invalid signature")
    safe_k1 = escape_valkey_tag(k1)
    q = Query(f"@ln_k1:{{{safe_k1}}}")
    res = vk.ft("idx:ln_k1").search(q)
    if res.total == 1:
        tx_id = res.docs[0]["id"].split(":")[-1]
        tx = Transaction.load(TransactionTypes.ln_oidc_login.value, tx_id)
        # TODO: Exception handling here
        # could be that a valid signature is presented but the device doesn't exist
        device = session.exec(select(Device).where(Device.pubkey == key)).one()
        user = session.exec(select(User).where(User.id == device.user_id)).one()
        tx.add_private_data(".user", {"uid": user.id, "device-id": device.id})
        await store_oidc_code(tx)
        tx.set_state("confirmed")
    return None


@router.post("/qr", responses={404: {"model": ErrorResponse}})
def qr_gen(rq: Transaction) -> QRDataResponse:
    """Generates a QR code for the frontend"""
    tx = Transaction.load(rq.tx_type.value, rq.tx_id)
    if tx.tx_type is TransactionTypes.ln_oidc_login:
        endpoint = "authenticate"
        action = "login"
    elif tx.tx_type is TransactionTypes.onboarding:
        endpoint = "register"
        action = "register"
    else:
        # TODO: Proper status code
        raise HTTPException(status_code=404, detail="Invalid transaction type")
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    elif "ln" not in tx.data or "k1" not in tx.data["ln"]:
        # TODO: Choose a more suitable status code
        raise HTTPException(status_code=404, detail="k1 not present in transaction")
    link = "{}/lnurl-auth/{}?k1={}&tag={}&action={}".format(server_url, endpoint, tx.data["ln"]["k1"], "login", action)
    qr_content = "lightning:{}".format(bech32.encode_bytes("lnurl", link.encode()))
    qr_image = generate_qr(qr_content)
    return QRDataResponse(link=qr_content, qr_image=qr_image)
