from sqlmodel import Field, SQLModel
from pydantic import BaseModel

from datetime import datetime


# Responses
class GenericResponse(BaseModel):
    status: str


# TODO: Implement and actually use - don't know how yet
# the FastAPI SQL guide will likely have an answer
class SuccessResponse(GenericResponse):
    status: str = "success"
    data: dict


class ErrorResponse(GenericResponse):
    status: str = "error"
    detail: str



class OnboardingLink(SQLModel, table=True):
    link_id: str = Field(index=True, primary_key=True)


# Unused?
class Token(BaseModel):
    value: str
    type: str
    expiration: datetime | None


class UserRegistrationToken(Token):
    type: str = "user_registration"


# Unused for now
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    mail: str = Field(index=True)


class RegistrationRequest(BaseModel):
    pubkey: str
    user_id: int | None = None
