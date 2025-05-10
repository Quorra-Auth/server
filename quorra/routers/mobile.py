from typing import Annotated

from fastapi import APIRouter, Header
from sqlmodel import select

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from uuid import uuid4
import json

from ..classes import RegistrationRequest, User, Device
from ..classes import ErrorResponse

from ..database import SessionDep
from ..database import vk

from ..utils import generate_qr
from ..config import server_url


router = APIRouter()

@router.post("/register", status_code=201, response_model=None, responses={403: {"model": ErrorResponse}})
async def register(rq: RegistrationRequest, session: SessionDep, x_registration_token: Annotated[str, Header()]):
    """Finishes device registration.

    Can either use a user or a device registration token.

    If a device registration token is used, a user ID is also required.
    The device will be added to the matched user.

    If a user registration token is used, a new user is created.
    """
    # TODO: Adding a new device to an existing user
    # OPTION 1 - new user registration
    urt: str = "user-registration:{}".format(x_registration_token)
    drt: str = "device-registration:{}".format(x_registration_token)
    if vk.exists(urt):
        u: User = User()
        session.add(u)
        session.commit()
        session.refresh(u)
        vk.delete(urt)
        uid: int = u.id
    # OPTION 2 - user exists, only register device
    # TODO: Fill with logic to find the user ID
    elif vk.exists(drt):
        pass
    else:
        raise HTTPException(status_code=403, detail="Token invalid")
    d: Device = Device(**rq.dict(), user_id=uid)
    session.add(d)
    session.commit()
    session.refresh(d)
    return None

