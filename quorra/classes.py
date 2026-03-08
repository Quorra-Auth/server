from sqlmodel import Field, SQLModel
from pydantic import BaseModel, field_serializer, computed_field
from enum import Enum
from typing import Literal
from datetime import datetime

from uuid import uuid4

from .database import vk
from valkey.commands.json.path import Path


class ErrorResponse(BaseModel):
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

class QRDataResponse(BaseModel):
    link: str
    qr_image: str

class DeviceRegistrationRequest(SQLModel):
    pubkey: str = Field(unique=True)
    name: str | None = None

class Device(DeviceRegistrationRequest, table=True):
    id: str = Field(primary_key=True)
    user_id: str = Field(default=None, foreign_key="user.id")


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["Bearer"] = "Bearer"
    id_token: str


class TransactionTypes(str, Enum):
    onboarding = "onboarding"
    ln_oidc_login = "ln-oidc-login"

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
    _expiry: int = 30
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

    def check_state_transition(self, state_from, state_to):
        """Dummy function - to be overridden by individual transaction types"""
        return True

    def set_state(self, state):
        if self.check_state_transition(self.state, state):
            vk.json().set(self._key_name, "$.state", state)

    def add_data(self, path, data):
        vk.json().set(self._key_name, "$.data{}".format(path), data)

    def add_private_data(self, path, data):
        vk.json().set(self._key_name, "$.private{}".format(path), data)

    def set_contents(self, contents):
        vk.json().set(self._key_name, Path.root_path(), contents)

    def prolong(self, expiry: int | None = None):
        if expiry is None:
            expiry = self._expiry
        vk.expire(self._key_name, expiry)

    def delete(self):
        vk.delete(self._key_name)

class OnboardingTransactionStates(str, Enum):
    created = "created"
    filled = "user-info-filled"
    finished = "finished"

class OnboardingTransaction(Transaction):
    # TODO: Move transition checks here
    tx_type: TransactionTypes = TransactionTypes.onboarding

class LnOIDCLoginTransaction(Transaction):
    tx_type: TransactionTypes = TransactionTypes.ln_oidc_login

class LnOIDCLoginTransactionStates(str, Enum):
    created = "created"
    identified = "identified"
    confirmed = "confirmed"
    finished = "finished"


class LNStatusEnum(str, Enum):
    ok = "OK"
    error = "error"

class LNStatusResponse(BaseModel):
    status: LNStatusEnum
    reason: str | None = None
