from typing import Annotated

from fastapi import APIRouter, Header
from sqlmodel import select

from fastapi import HTTPException

from uuid import uuid4
import json
import base64

from ..classes import DeviceRegistrationRequest, User, Device, Transaction
from ..classes import AQRMobileIdentifyRequest, AQRMobileAuthenticateRequest
from ..classes import ErrorResponse, AqrOIDCLoginTransactionStates

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

from valkey.commands.search.query import Query

from .oidc import store_oidc_code

from ..database import SessionDep
from ..database import vk

from ..utils import generate_qr
from ..utils import escape_valkey_tag
from ..config import server_url

router = APIRouter()

# TODO: Return the device ID for future use as a hint for the server
@router.post("/register", status_code=201, response_model=None, responses={403: {"model": ErrorResponse}})
async def register_device(rq: DeviceRegistrationRequest, session: SessionDep, x_registration_token: Annotated[str, Header()]):
    """Finishes device registration.

    Can either use a user or a device registration token.

    If a device registration token is used, a user ID is also required.
    The device will be added to the matched user.

    If a user registration token is used, a new user is created.
    """
    # OPTION 1 - new user registration
    safe_token = escape_valkey_tag(x_registration_token)
    q = Query(f"@device_registration_token:{{{safe_token}}}")
    res = vk.ft("idx:device_registration_token").search(q)
    if res.total == 1:
        # Finds the matching transaction
        tx_id = res.docs[0]["id"].split(":")[-1]
        tx = Transaction.load("onboarding", tx_id)
        user_details = tx._private_data["entry"]
        u: User = User(id=str(uuid4()), username=user_details["username"], email=user_details["email"])
        session.add(u)
        session.commit()
        session.refresh(u)
        tx.set_state("finished")
        uid: int = u.id
    # TODO: Adding a new device to an existing user
    # TODO: OPTION 2 - user exists, only register device
    # TODO: Fill with logic to find the user ID
    else:
        raise HTTPException(status_code=403, detail="Token invalid")
    d: Device = Device(**rq.dict(), user_id=uid, id=str(uuid4()))
    session.add(d)
    session.commit()
    session.refresh(d)
    return None


# TODO: Use UUID hints from the device
@router.post("/aqr/identify", response_model=None, responses={403: {"model": ErrorResponse}})
async def aqr_identify(rq: AQRMobileIdentifyRequest, db_session: SessionDep, session: str):
    tx = Transaction.load("aqr-oidc-login", session)
    if tx.state != AqrOIDCLoginTransactionStates.created.value:
        raise HTTPException(status_code=403, detail="Session already identified")
    devices = db_session.exec(select(Device)).all()
    device_found = False
    for device in devices:
        key = ed25519.Ed25519PublicKey.from_public_bytes(base64.b64decode(device.pubkey))
        try:
            key.verify(base64.b64decode(rq.signature), rq.message.encode('utf-8'))
        except InvalidSignature:
            pass
        else:
            device_found = True
            matched_device = device
            break
    if device_found:
        tx.add_private_data(".user", {"device-id": matched_device.id})
        tx.set_state("identified")
    else:
        raise HTTPException(status_code=403, detail="No matching device")
    return None


@router.post("/aqr/authenticate", response_model=None, responses={404: {"model": ErrorResponse}})
async def aqr_authenticate(rq: AQRMobileAuthenticateRequest, db_session: SessionDep, session: str):
    tx = Transaction.load("aqr-oidc-login", session)
    device_id = tx._private_data["user"]["device-id"]
    device = db_session.exec(select(Device).where(Device.id == device_id)).one()
    key = ed25519.Ed25519PublicKey.from_public_bytes(base64.b64decode(device.pubkey))
    try:
        key.verify(base64.b64decode(rq.signature), rq.message.encode('utf-8'))
    except InvalidSignature:
        raise HTTPException(status_code=403, detail="Signature invalid")
    else:
        if rq.state == "accepted":
            user = db_session.exec(select(User).where(User.id == device.user_id)).one()
            tx.add_private_data(".user", {"uid": user.id})
            await store_oidc_code(tx)
            tx.set_state("confirmed")
        elif rq.state == "rejected":
            pass
            # TODO: Figure out what to do here
    return None
