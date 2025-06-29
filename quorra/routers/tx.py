from typing import Annotated

from fastapi import APIRouter, Header
from sqlmodel import select

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from uuid import uuid4
import json
import base64

from ..classes import Transaction, TransactionCreateRequest, TransactionUpdateRequest
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


@router.get("/transaction", status_code=200, response_model=Transaction, responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
async def get_transaction(tx_type: TransactionTypes, tx_id: str, session: SessionDep):
    """Get transaction."""
    tx = Transaction.load(tx_type.value, tx_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    tx.prolong()
    return tx

@router.post("/transaction", status_code=201, response_model=Transaction, responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
async def create_transaction(rq: TransactionCreateRequest, session: SessionDep):
    """Start a new transaction."""
    tx = Transaction.new(rq.tx_type.value)
    return tx
