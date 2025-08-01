from sqlmodel import Field, SQLModel
from pydantic import BaseModel, field_serializer, PrivateAttr, computed_field
from enum import Enum
from typing import Literal
from datetime import datetime

from uuid import uuid4

from .database import vk


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

class RegistrationResponse(BaseModel):
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

class TransactionCreateRequest(BaseModel):
    tx_type: TransactionTypes

class TransactionUpdateRequest(TransactionCreateRequest):
    tx_id: str
    data: dict

class Transaction(BaseModel):
    tx_type: TransactionTypes
    tx_id: str | None = None

    _data_key: str
    _state_key: str
    _private_data_key: str
    _expiry: int = 5

    def __init__(self, **data):
        super().__init__(**data)
        base_key : str = "{}:{}".format(self.tx_type.value, self.tx_id)
        # Apparently Pydantic intercepts normal assignments, so...
        object.__setattr__(self, "_data_key", base_key)
        object.__setattr__(self, "_state_key", base_key + ":state")
        object.__setattr__(self, "_private_data_key", base_key + ":private-data")

    @computed_field
    @property
    def state(self) -> str:
        return vk.get(self._state_key)

    def _cleanup_dict(self, d: dict) -> dict:
        """Workaround - Valkey won't store an empty dict"""
        if "empty" in d:
            return {}
        return d

    @computed_field
    @property
    def data(self) -> dict:
        return self._cleanup_dict(dict(vk.hgetall(self._data_key)))

    @property
    def _private_data(self) -> dict:
        return self._cleanup_dict(dict(vk.hgetall(self._private_data_key)))

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
        tx.save_state("created")
        tx.save_data({}, True)
        tx.save_data({}, False)
        return tx

    def save_state(self, state: str):
        vk.set(self._state_key, state)
        vk.expire(self._state_key, self._expiry)

    def save_data(self, data: dict, public: bool):
        if public:
            key = self._data_key
        else:
            key = self._private_data_key
        self._save_data(key, data)

    def _save_data(self, key: str, data: dict):
        if len(data) == 0:
            data = {"empty": ""}
        vk.hset(key, mapping=data)
        vk.expire(key, self._expiry)

    def add_data(self, data: dict, public: bool):
        if public:
            key = self._data_key
        else:
            key = self._private_data_key
        self._add_data(key, data)

    def _add_data(self, key: str, data: dict):
        orig = vk.hgetall(self._data_key)
        new = orig | data
        vk.hset(key, mapping=new)
        vk.expire(key, self._expiry)

    def prolong(self):
        for key in [self._data_key, self._state_key, self._private_data_key]:
            vk.expire(key, self._expiry)

    def delete(self):
        vk.delete(self._state_key)
        vk.delete(self._data_key)

class OnboardingTransactionStates(str, Enum):
    created = "created"
    filled = "user-info-filled"
    finished = "finished"

class OnboardingTransaction(Transaction):
    tx_type: TransactionTypes = TransactionTypes.onboarding
