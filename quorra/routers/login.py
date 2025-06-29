from typing import Annotated, Union

from fastapi import APIRouter, Header
from sqlmodel import select

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from uuid import uuid4
import json

from ..classes import SessionStartResponse
from ..classes import UnauthenticatedPollResponse, AuthenticatedPollResponse
from ..classes import Device
from ..classes import ErrorResponse

from ..vk_helpers import vk_session, vk_oidc_code

from ..database import SessionDep
from ..database import vk

from ..utils import generate_qr
from ..utils import QRCodeResponse
from ..config import server_url


router = APIRouter()


@router.get("/start", status_code=201)
async def login_start(client_id: str, scope: str, nonce: str | None = None) -> SessionStartResponse:
    """Starts a new login session."""
    session_id: str = str(uuid4())
    qr_content = "quorra+{}/mobile/login?s={}".format(server_url, session_id)
    qr_image = generate_qr(qr_content)
    vk_s = vk_session(session_id)
    oidc_context = {"client-id": client_id, "scope": scope}
    if nonce is not None:
        oidc_context["nonce"] = nonce
    vk.hset(vk_s, mapping=oidc_context)
    vk.expire(vk_s, 15)
    return SessionStartResponse(session_id=session_id, expiration=vk.expiretime(vk_s), qr_image=qr_image)


async def store_oidc_code(session_id: str, code: str):
    vk_s: str = vk_session(session_id)
    vk_uid: str = vk_s + ":user-id"
    vk_did: str = vk_s + ":device-id"
    vk_code: str = vk_oidc_code(code)

    oidc_context: dict = vk.hgetall(vk_s)
    session_context: dict = oidc_context
    session_context["user-id"] = vk.get(vk_uid)
    session_context["device-id"] = vk.get(vk_did)

    vk.delete(vk_s)
    vk.delete(vk_uid)
    vk.delete(vk_did)
    vk.hset(vk_code, mapping=session_context)
    vk.expire(vk_code, 15)


@router.get("/fepoll", responses={404: {"model": ErrorResponse}})
async def fe_poll(db_session: SessionDep, session: str) -> UnauthenticatedPollResponse | AuthenticatedPollResponse:
    """Checks the session state."""
    vk_s: str = vk_session(session)
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
    vk_session: str = "session:{}".format(session)
    if vk.exists(vk_session):
        vk.expire(vk_session, 15)
        vk_uid: str = vk_session + ":user-id"
        vk_did: str = vk_session + ":device-id"
        if vk.exists(vk_uid):
            device_id = vk.get(vk_did)
            device = db_session.exec(select(Device).where(Device.id == device_id)).one()
            return AuthenticatedPollResponse(device_id=device_id, device_name=device.name, user_id=vk.get(vk_uid), expiration=vk.expiretime(vk_session))
        elif vk.exists(vk_did):
            device_id = vk.get(vk_did)
            device = db_session.exec(select(Device).where(Device.id == device_id)).one()
            return IdentifiedPollResponse(device_id=device_id, device_name=device.name, expiration=vk.expiretime(vk_session))
        else:
            return WaitingPollResponse(expiration=vk.expiretime(vk_session))
    else:
        raise HTTPException(status_code=404, detail="Session not found")
