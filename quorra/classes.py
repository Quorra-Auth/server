from sqlmodel import Field, SQLModel
from pydantic import BaseModel, field_serializer, PrivateAttr, computed_field
from enum import Enum
from typing import Literal
from datetime import datetime

from uuid import uuid4

from .database import vk
from valkey.commands.json.path import Path


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
    username: str
    email: str


class RegistrationRequest(BaseModel):
    link_id: str

class OnboardingDataResponse(BaseModel):
    link: str
    qr_image: str

class EntryRequest(BaseModel):
    username: str
    email: str

class DeviceRegistrationRequest(SQLModel):
    pubkey: str
    name: str | None = None

class Device(DeviceRegistrationRequest, table=True):
    id: str = Field(primary_key=True)
    user_id: str = Field(default=None, foreign_key="user.id")


class SessionResponse(BaseModel):
    state: str
    # UNIX timestamp - always expires in 15 seconds, polling prolongs the session
    expiration: int

class SessionStartResponse(SessionResponse):
    state: Literal["created"] = "created"
    session_id: str
    qr_image: str

class UnauthenticatedSessionState(str, Enum):
    waiting = "waiting"
    identified = "identified"

class UnauthenticatedPollResponse(SessionResponse):
    state: UnauthenticatedSessionState

class AuthenticatedPollResponse(SessionResponse):
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


class TokenResponse(BaseModel):
    access_token: str = "dummy-access-token"
    token_type: Literal["Bearer"] = "Bearer"
    id_token: str


class TransactionTypes(str, Enum):
    onboarding = "onboarding"
    oidc_login = "oidc-login"

class TransactionGetRequest(BaseModel):
    tx_type: TransactionTypes
    tx_id: str

class TransactionCreateRequest(BaseModel):
    tx_type: TransactionTypes

# NOTE: The semantics of this might change
class TransactionUpdateRequest(TransactionCreateRequest):
    tx_id: str
    data: dict

class Transaction(BaseModel):
    tx_type: TransactionTypes
    tx_id: str | None = None

    # TODO: shorten
    _expiry: int = 500
    _key_name: str | None = None

    def __init__(self, **data):
        super().__init__(**data)
        object.__setattr__(self, "_key_name", "{}:{}".format(self.tx_type.value, self.tx_id))

    @computed_field
    @property
    def state(self) -> str:
        return vk.json().get(self._key_name)["state"]

    @computed_field
    @property
    def data(self) -> dict:
        return vk.json().get(self._key_name)["data"]

    @property
    def _private_data(self) -> dict:
        return vk.json().get(self._key_name)["private"]

    @field_serializer("state", "data")
    def serialize_computed_fields(self, value, _info):
        return value

    @classmethod
    def load(cls, tx_type: str, tx_id: str) -> "Transaction | None":
        if not vk.exists("{}:{}".format(tx_type, tx_id)):
            return None
        return cls(tx_id=tx_id, tx_type=tx_type)

    @classmethod
    def new(cls, tx_type: str) -> "Transaction":
        tx = cls(tx_id=str(uuid4()), tx_type=tx_type)
        initial_contents: dict = {"state": "created", "data": {}, "private": {}}
        tx.set_contents(initial_contents)
        return tx

    def set_state(self, state):
        vk.json().set(self._key_name, "$.state", state)

    def add_data(self, path, data):
        vk.json().set(self._key_name, "$.data{}".format(path), data)

    def add_private_data(self, path, data):
        vk.json().set(self._key_name, "$.private{}".format(path), data)

    def set_contents(self, contents):
        vk.json().set(self._key_name, Path.root_path(), contents)

    def prolong(self):
        vk.expire(self._key_name, self._expiry)

    def delete(self):
        vk.delete(self._key_name)

class OnboardingTransactionStates(str, Enum):
    created = "created"
    filled = "user-info-filled"
    finished = "finished"

class OnboardingTransaction(Transaction):
    tx_type: TransactionTypes = TransactionTypes.onboarding
