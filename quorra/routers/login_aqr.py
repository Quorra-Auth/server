from typing import Annotated, Union

from fastapi import APIRouter, Header
from sqlmodel import select

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from uuid import uuid4
import json

from ..classes import AQRSessionResponse, AQRSessionInitResponse
from ..classes import AQRSessionWaitingPollResponse, AQRSessionIdentifiedPollResponse, AQRSessionAuthenticatedPollResponse
from ..classes import ErrorResponse

from ..database import SessionDep
from ..database import vk

from ..utils import generate_qr
from ..utils import QRCodeResponse
from ..config import server_url


router = APIRouter()

# Maybe secure using an API key? x_idp_api_key: Annotated[str, Header()]


@router.get("/start", status_code=201, response_model=AQRSessionInitResponse)
async def aqr_start() -> AQRSessionInitResponse:
    """Starts a new AQR login session."""
    session_id: str = str(uuid4())
    aqr_vk_session: str = "aqr-session:{}".format(session_id)
    vk.set(aqr_vk_session, 1, ex=15)
    return AQRSessionInitResponse(session_id=session_id, expiration=vk.expiretime(aqr_vk_session))


# TODO: Actually make a QR code
@router.get("/code", response_class=QRCodeResponse, responses={404: {"model": ErrorResponse}})
async def aqr_code(session: str) -> QRCodeResponse:
    """Returns a rendered QR code for a given session"""
    return None


@router.get("/poll", responses={404: {"model": ErrorResponse}})
async def aqr_poll(db_session: SessionDep, session: str) -> AQRSessionWaitingPollResponse | AQRSessionIdentifiedPollResponse | AQRSessionAuthenticatedPollResponse:
    """Checks the AQR session state."""
    aqr_vk_session = "aqr-session:{}".format(session)
    if vk.exists(aqr_vk_session):
        vk.expire(aqr_vk_session, 15)
        vk_uid: str = aqr_vk_session + ":user-id"
        vk_did: str = aqr_vk_session + ":device-id"
        if vk.exists(vk_uid):
            # TODO: device name from DB
            return AQRSessionAuthenticatedPollResponse(device_id=vk.get(vk_did), device_name=None, user_id=vk.get(vk_uid), expiration=vk.expiretime(aqr_vk_session))
        elif vk.exists(vk_did):
            return AQRSessionIdentifiedPollResponse(device_id=vk.get(vk_did), expiration=vk.expiretime(aqr_vk_session))
        else:
            return AQRSessionWaitingPollResponse(expiration=vk.expiretime(aqr_vk_session))
    else:
        raise HTTPException(status_code=404, detail="Session not found")

