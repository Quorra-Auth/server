from typing import Annotated

from fastapi import APIRouter, Header
from sqlmodel import select

from fastapi import HTTPException

from uuid import uuid4
import json
import base64

from ..classes import Transaction, TransactionCreateRequest, TransactionGetRequest
from ..classes import TransactionTypes
from ..classes import ErrorResponse

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

from ..database import SessionDep
from ..database import vk

from ..utils import generate_qr
from ..config import server_url


router = APIRouter()


@router.post("/transaction", status_code=200, response_model=Transaction, responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
async def get_transaction(rq: TransactionGetRequest) -> Transaction:
    """Get and prolong a transaction."""
    # TODO: Prolong tokens and separate endpoint for prolonging transactions
    tx = Transaction.load(rq.tx_type.value, rq.tx_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if tx.state != "finished":
        tx.prolong()
    return tx
