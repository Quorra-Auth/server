from sqlmodel import Field, SQLModel
from pydantic import BaseModel
from enum import Enum
from typing import Literal

from datetime import datetime


# Responses
class GenericResponse(BaseModel):
    status: str


# Probably remove
class SuccessResponse(GenericResponse):
    status: Literal["success"] = "success"
    data: dict


class ErrorResponse(GenericResponse):
    status: Literal["error"] = "error"
    detail: str



class OnboardingLink(SQLModel, table=True):
    link_id: str = Field(index=True, primary_key=True)


class User(SQLModel, table=True):
    id: str = Field(primary_key=True)


class DeviceRegistrationRequest(SQLModel):
    pubkey: str
    name: str | None = None

class Device(DeviceRegistrationRequest, table=True):
    id: str = Field(primary_key=True)
    user_id: int = Field(default=None, foreign_key="user.id")


class AQRSessionResponse(BaseModel):
    state: str
    # UNIX timestamp - always expires in 15 seconds, polling prolongs the session
    expiration: int

class AQRSessionStartResponse(AQRSessionResponse):
    state: Literal["created"] = "created"
    session_id: str

class AQRUnauthenticatedSessionState(str, Enum):
    waiting = "waiting"
    identified = "identified"

class AQRSessionUnauthenticatedPollResponse(AQRSessionResponse):
    state: AQRUnauthenticatedSessionState

class AQRSessionAuthenticatedPollResponse(AQRSessionResponse):
    state: Literal["authenticated"] = "authenticated"
    code: str


class AQRMobileStateEnum(str, Enum):
    accepted = "accepted"
    rejected = "rejected"

# TODO: Send a device UUID as well so that the server can get a hint
class AQRMobileIdentifyRequest(BaseModel):
    signature: str
    message: str

class AQRMobileAuthenticateRequest(BaseModel):
    state: AQRMobileStateEnum
    signature: str
    message: str
