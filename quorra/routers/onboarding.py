from typing import Annotated

from fastapi import APIRouter, Header
from sqlmodel import select

from fastapi import HTTPException

from uuid import uuid4
import json

from ..classes import OnboardingLink
from ..classes import ErrorResponse

from ..database import SessionDep
from ..database import vk

from ..utils import generate_qr
from ..utils import QRCodeResponse
from ..config import server_url


router = APIRouter()

# Should probably return the server URL as well
@router.get("/init", status_code=201, response_model=OnboardingLink, responses={403: {"model": ErrorResponse}})
async def onboard(session: SessionDep, x_self_service_token: Annotated[str | None, Header()] = None) -> OnboardingLink:
    authenticated: bool = False
    # If users are empty and onboarding links are empty, we allow it
    # TODO: Check if users are empty
    if len(session.exec(select(OnboardingLink)).all()) == 0:
        authenticated = True
    # If a valid self-service token is presented, we allow it
    if x_self_service_token is not None:
        authenticated = True
    if not authenticated:
        raise HTTPException(status_code=403, detail="x-self-service-token missing or invalid")
    link: OnboardingLink = OnboardingLink(link_id=str(uuid4()))
    session.add(link)
    session.commit()
    session.refresh(link)
    return link


@router.get("/register/{onboarding_link}", response_class=QRCodeResponse, responses={404: {"model": ErrorResponse}})
async def register_user(session: SessionDep, onboarding_link: str) -> QRCodeResponse:
    """Users are intended to go to this URL to finish their onboarding.

    They'll get a rendered user registration QR code. Scanning this code will
    finish user registration.

    The generated QR code is valid for 2 hours.
    \f
    Generates a user registration token -> stores in Valkey
    Returns a rendered QR code PNG"""

    l = session.get(OnboardingLink, onboarding_link)
    if not l:
        raise HTTPException(status_code=404, detail="Onboarding link not found")
    token: str = str(uuid4())
    qr_content = "quorra+{}/mobile/register?t={}".format(server_url, token)
    vk.set("user-registration:{}".format(token), 1, ex=7200)
    session.delete(l)
    session.commit()
    # For debugging the mobile app
    print(token)
    code = generate_qr(qr_content)
    return code
