from sqlmodel import Field, SQLModel
from pydantic import BaseModel, field_serializer, computed_field
from enum import Enum
from typing import ClassVar, Literal
from datetime import datetime

from uuid import uuid4

from .database import vk
from .utils import escape_valkey_tag
from .valkey_indexes import register_index, search as vk_search
from valkey.commands.search.query import Query
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

class DuplicateTransactionMatch(Exception):
    pass


class Transaction(BaseModel):
    tx_type: TransactionTypes
    tx_id: str | None = None

    # alias -> JSON path. Each (type, alias) gets its own index over this type's keys.
    indexes: ClassVar[dict[str, str]] = {}

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
    def __pydantic_init_subclass__(cls, **kwargs):
        super().__pydantic_init_subclass__(**kwargs)
        tx_type = cls.model_fields["tx_type"].default
        for alias, path in cls.indexes.items():
            register_index(tx_type.value, alias, path)

    @classmethod
    def find_by(cls, alias: str, value: str) -> "Transaction | None":
        """Look up a transaction of this type by an indexed field.
        Returns None if nothing matches; raises if the value is ambiguous."""
        if alias not in cls.indexes:
            raise ValueError("{} has no index {}".format(cls.__name__, alias))
        tx_type = cls.model_fields["tx_type"].default
        q = Query("@{}:{{{}}}".format(alias, escape_valkey_tag(value)))
        res = vk_search("idx:{}:{}".format(tx_type.value, alias), q)
        if res.total == 0:
            return None
        if res.total > 1:
            raise DuplicateTransactionMatch("{} matched {} transactions".format(alias, res.total))
        tx_id = res.docs[0]["id"].split(":", 1)[1]
        return cls.load(tx_type.value, tx_id)

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
    indexes: ClassVar[dict[str, str]] = {"ln_k1": "$.data.ln.k1"}

class LnOIDCLoginTransaction(Transaction):
    tx_type: TransactionTypes = TransactionTypes.ln_oidc_login
    indexes: ClassVar[dict[str, str]] = {
        "ln_k1": "$.data.ln.k1",
        "oidc_code": "$.data.oidc_data.code",
        "oidc_at": "$.private.oidc_data.access_token",
    }

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
