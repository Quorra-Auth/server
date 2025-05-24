from fastapi import APIRouter

from fastapi import HTTPException

from uuid import uuid4
import json

from ..classes import ErrorResponse

from ..vk_helpers import vk_session

from ..database import vk

from ..utils import generate_qr
from ..utils import QRCodeResponse
from ..config import server_url


router = APIRouter()


@router.get("/code", response_class=QRCodeResponse, responses={404: {"model": ErrorResponse}})
async def aqr_code(session: str) -> QRCodeResponse:
    """Returns a rendered QR code for a given session"""
    aqr_vk_session: str = vk_session(session)
    if vk.exists(aqr_vk_session):
        qr_content = "quorra+{}/mobile/login?s={}".format(server_url, session)
        code = generate_qr(qr_content)
        return code
    else:
        raise HTTPException(status_code=404, detail="Session not found")
