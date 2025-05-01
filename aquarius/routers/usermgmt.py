from typing import Annotated

from fastapi import APIRouter, Query, Header
from sqlmodel import Field, SQLModel, select

from fastapi import HTTPException
from pydantic_core import ValidationError

from uuid import uuid4

from ..classes.onboarding_link import OnboardingLink
from ..classes.user import User

from ..common import ErrorMessage
from ..database import SessionDep

router = APIRouter()

@router.get("/onboard", status_code=201, response_model=OnboardingLink, responses={403: {"model": ErrorMessage}})
def onboard(session: SessionDep, x_session_token: Annotated[str | None, Header()] = None) -> OnboardingLink:
    authenticated: bool = False
    # If users are empty and onboarding links are empty, we allow it
    # TODO: Check if users are empty
    if len(session.exec(select(OnboardingLink)).all()) == 0:
        authenticated = True
    # If a valid session token is presented, we allow it
    if x_session_token is not None:
        authenticated = True
    if not authenticated:
        raise HTTPException(status_code=403, detail="x-session-token missing or invalid")
    link: OnboardingLink = OnboardingLink(link_id=str(uuid4()))
    session.add(link)
    session.commit()
    session.refresh(link)
    return link

# Only consumes onboarding links for now
# Should return the user registration QR
# Needs to know:
#   the server URL to encode
#   needs to generate an onboarding session token
#

@router.get("/register/{onboarding_link}", status_code=200, responses={404: {"model": ErrorMessage}})
def register_user(session: SessionDep, onboarding_link: str):
    l = session.get(OnboardingLink, onboarding_link)
    if not l:
        raise HTTPException(status_code=404, detail="Onboarding link not found")
    session.delete(l)
    session.commit()
    return {"msg": "Onboarding link consumed!"}
