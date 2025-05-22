from typing import Annotated, Union

from fastapi import APIRouter, Header
from sqlmodel import select

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from uuid import uuid4
import json

from ..classes import AQRSessionResponse, AQRSessionStartResponse
from ..classes import AQRSessionUnauthenticatedPollResponse, AQRSessionAuthenticatedPollResponse
from ..classes import Device
from ..classes import ErrorResponse

from ..database import SessionDep
from ..database import vk

from ..utils import generate_qr
from ..utils import QRCodeResponse
from ..config import server_url


router = APIRouter()


@router.get("/start", status_code=201)
async def aqr_start() -> AQRSessionStartResponse:
    """Starts a new AQR login session."""
    session_id: str = str(uuid4())
    aqr_vk_session: str = "aqr-session:{}".format(session_id)
    vk.set(aqr_vk_session, 1, ex=15)
    return AQRSessionStartResponse(session_id=session_id, expiration=vk.expiretime(aqr_vk_session))


@router.get("/code", response_class=QRCodeResponse, responses={404: {"model": ErrorResponse}})
async def aqr_code(session: str) -> QRCodeResponse:
    """Returns a rendered QR code for a given session"""
    aqr_vk_session: str = "aqr-session:{}".format(session)
    if vk.exists(aqr_vk_session):
        qr_content = "quorra+{}/mobile/login?s={}".format(server_url, session)
        code = generate_qr(qr_content)
        return code
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/fepoll", responses={404: {"model": ErrorResponse}})
async def aqr_fe_poll(db_session: SessionDep, session: str) -> AQRSessionUnauthenticatedPollResponse | AQRSessionAuthenticatedPollResponse:
    """Checks the AQR session state."""
    aqr_vk_session: str = "aqr-session:{}".format(session)
    if vk.exists(aqr_vk_session):
        vk.expire(aqr_vk_session, 15)
        vk_uid: str = aqr_vk_session + ":user-id"
        vk_did: str = aqr_vk_session + ":device-id"
        if vk.exists(vk_uid):
            vk.delete(aqr_vk_session)
            vk.delete(vk_uid)
            vk.delete(vk_did)
            # TODO: Bind the code to a user and device so that we can later fill the id_token
            return AQRSessionAuthenticatedPollResponse(code=str(uuid4()), expiration=vk.expiretime(aqr_vk_session))
        elif vk.exists(vk_did):
            device_id = vk.get(vk_did)
            device = db_session.exec(select(Device).where(Device.id == device_id)).one()
            return AQRSessionUnauthenticatedPollResponse(state="identified", expiration=0)
        else:
            return AQRSessionUnauthenticatedPollResponse(state="waiting", expiration=vk.expiretime(aqr_vk_session))
    else:
        raise HTTPException(status_code=404, detail="Session not found")


# TODO: TBD
@router.get("/bepoll", responses={404: {"model": ErrorResponse}})
async def aqr_be_poll(db_session: SessionDep, session: str) -> None:
    return None
    aqr_vk_session: str = "aqr-session:{}".format(session)
    if vk.exists(aqr_vk_session):
        vk.expire(aqr_vk_session, 15)
        vk_uid: str = aqr_vk_session + ":user-id"
        vk_did: str = aqr_vk_session + ":device-id"
        if vk.exists(vk_uid):
            device_id = vk.get(vk_did)
            device = db_session.exec(select(Device).where(Device.id == device_id)).one()
            return AQRSessionAuthenticatedPollResponse(device_id=device_id, device_name=device.name, user_id=vk.get(vk_uid), expiration=vk.expiretime(aqr_vk_session))
        elif vk.exists(vk_did):
            device_id = vk.get(vk_did)
            device = db_session.exec(select(Device).where(Device.id == device_id)).one()
            return AQRSessionIdentifiedPollResponse(device_id=device_id, device_name=device.name, expiration=vk.expiretime(aqr_vk_session))
        else:
            return AQRSessionWaitingPollResponse(expiration=vk.expiretime(aqr_vk_session))
    else:
        raise HTTPException(status_code=404, detail="Session not found")
