from typing import Annotated

from fastapi import APIRouter, Header
from sqlmodel import select

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from uuid import uuid4
import json

from ..classes import OnboardingLink
from ..classes import UserRegistrationToken
from ..classes import ErrorResponse
from ..classes import RegistrationRequest

from ..database import SessionDep
from ..database import vk

from ..utils import generate_qr


router = APIRouter()

@router.post("/register", status_code=201, response_model=None, responses={403: {"model": ErrorResponse}})
async def register(rq: RegistrationRequest, session: SessionDep, x_registration_token: Annotated[str, Header()]):
    """Finishes device registration.

    Can either use a user or a device registration token.

    If a device registration token is used, a user ID is also required.
    The device will be added to the matched user.

    If a user registration token is used, a new user is created.
    """
    print(rq.pubkey)
    rt: str = "registration:{}".format(x_registration_token)
    # TODO: Adding a new device to an existing user
    if rq.user_id is not None:
        return {"Not implemented"}
    # OPTION 1 - only a token is sent
    elif vk.exists(rt):
        vk.delete(rt)
        return {"Token {} deleted".format(rt)}
    return None

