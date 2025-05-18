from sqlmodel import Field, SQLModel
from pydantic import BaseModel

from datetime import datetime


# Responses
class GenericResponse(BaseModel):
    status: str


# Probably remove
class SuccessResponse(GenericResponse):
    status: str = "success"
    data: dict


class ErrorResponse(GenericResponse):
    status: str = "error"
    detail: str



class OnboardingLink(SQLModel, table=True):
    link_id: str = Field(index=True, primary_key=True)


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)


class RegistrationRequest(SQLModel):
    pubkey: str
    device_name: str | None = None

# TODO: Use UUIDs
class Device(RegistrationRequest, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(default=None, foreign_key="user.id")


class AQRSessionResponse(BaseModel):
    state: str
    # UNIX timestamp - always expires in 15 seconds, polling prolongs the session
    expiration: int

class AQRSessionInitResponse(AQRSessionResponse):
    state: str = "created"
    session_id: str

class AQRSessionWaitingPollResponse(AQRSessionResponse):
    state: str = "waiting"

class AQRSessionIdentifiedPollResponse(AQRSessionWaitingPollResponse):
    state: str = "identified"
    device_id: str
    device_name: str | None = None

class AQRSessionAuthenticatedPollResponse(AQRSessionIdentifiedPollResponse):
    state: str = "authenticated"
    user_id: str
