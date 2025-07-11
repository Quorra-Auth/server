from typing import Annotated

from fastapi import APIRouter, Header
from sqlmodel import select

from fastapi import HTTPException

from uuid import uuid4
import json

from ..classes import OnboardingLink, User
from ..classes import RegistrationRequest, RegistrationResponse
from ..classes import ErrorResponse

from ..database import SessionDep
from ..database import vk

from ..utils import generate_qr
from ..utils import QRCodeResponse
from ..config import server_url
from ..config import config


router = APIRouter()

# TODO: Should probably return the server URL as well
@router.get("/init", status_code=201, response_model=OnboardingLink, responses={403: {"model": ErrorResponse}})
async def onboard(session: SessionDep, x_self_service_token: Annotated[str | None, Header()] = None) -> OnboardingLink:
    authenticated: bool = False
    # Bypass for when self-registrations are open
    if config["server"]["registrations"]:
        authenticated = True
    # If users and onboarding links are empty, we allow it
    elif len(session.exec(select(OnboardingLink)).all()) == 0 and len(session.exec(select(User)).all()) == 0:
        authenticated = True
    # TODO: If a valid self-service token is presented, we allow it
    # garbage condition for now
    elif x_self_service_token is not None and authenticated:
        authenticated = True
    if not authenticated:
        raise HTTPException(status_code=403, detail="x-self-service-token missing or invalid")
    link: OnboardingLink = OnboardingLink(link_id=str(uuid4()))
    session.add(link)
    session.commit()
    session.refresh(link)
    print("Debug only!!!")
    print("http://localhost:8080/fe/onboard/index.html?link={}".format(link.link_id))
    return link


@router.post("/register", responses={404: {"model": ErrorResponse}})
async def register_user(req: RegistrationRequest, session: SessionDep) -> RegistrationResponse:
    """Used by the frontend to generate a user registration token.


    The generated token is valid for 2 hours.
    \f
    Generates a user registration token -> stores in Valkey"""

    l = session.get(OnboardingLink, req.link_id)
    if not l:
        raise HTTPException(status_code=404, detail="Onboarding link not found")
    token: str = str(uuid4())
    link = "quorra+{}/mobile/register?t={}".format(server_url, token)
    qr_image = generate_qr(link)
    registration_details = {"username": req.username, "email": req.email}
    vk.hset("user-registration:{}".format(token), mapping=registration_details)
    vk.expire("user-registration:{}".format(token), 7200)

    session.delete(l)
    session.commit()
    return RegistrationResponse(link=link, qr_image=qr_image)
