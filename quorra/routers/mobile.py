from typing import Annotated

from fastapi import APIRouter, Header
from sqlmodel import select

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from uuid import uuid4
import json
import base64

from ..classes import DeviceRegistrationRequest, User, Device
from ..classes import AQRMobileIdentifyRequest, AQRMobileAuthenticateRequest
from ..classes import ErrorResponse

from ..vk_helpers import vk_session

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

from ..database import SessionDep
from ..database import vk

from ..utils import generate_qr
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
    urt: str = "user-registration:{}".format(x_registration_token)
    drt: str = "device-registration:{}".format(x_registration_token)
    if vk.exists(urt):
        u: User = User(id=str(uuid4()))
        session.add(u)
        session.commit()
        session.refresh(u)
        vk.delete(urt)
        uid: int = u.id
    # TODO: Adding a new device to an existing user
    # OPTION 2 - user exists, only register device
    # TODO: Fill with logic to find the user ID
    elif vk.exists(drt):
        pass
    else:
        raise HTTPException(status_code=403, detail="Token invalid")
    d: Device = Device(**rq.dict(), user_id=uid, id=str(uuid4()))
    session.add(d)
    session.commit()
    session.refresh(d)
    return None


# TODO: Use UUID hints from the device
# TODO: Session unidentify
@router.post("/aqr/identify", response_model=None, responses={403: {"model": ErrorResponse}})
async def aqr_identify(rq: AQRMobileIdentifyRequest, db_session: SessionDep, session: str):
    aqr_vk_session: str = vk_session(session)
    if vk.exists(aqr_vk_session + ":device-id"):
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
        vk.set(aqr_vk_session + ":device-id", matched_device.id, ex=3600)
    else:
        raise HTTPException(status_code=403, detail="No matching device")
    return None


@router.post("/aqr/authenticate", response_model=None, responses={404: {"model": ErrorResponse}})
async def aqr_authenticate(rq: AQRMobileAuthenticateRequest, db_session: SessionDep, session: str):
    aqr_vk_session: str = vk_session(session)
    device = db_session.exec(select(Device).where(Device.id == vk.get(aqr_vk_session + ":device-id"))).one()
    key = ed25519.Ed25519PublicKey.from_public_bytes(base64.b64decode(device.pubkey))
    try:
        key.verify(base64.b64decode(rq.signature), rq.message.encode('utf-8'))
    except InvalidSignature:
        raise HTTPException(status_code=403, detail="Signature invalid")
    else:
        # TODO: Implement rejection
        user = db_session.exec(select(User).where(User.id == device.user_id)).one()
        vk.set(aqr_vk_session + ":user-id", user.id, ex=3600)
    return None
