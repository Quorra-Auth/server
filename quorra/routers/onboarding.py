from typing import Annotated

from fastapi import APIRouter, Header
from sqlmodel import select

from fastapi import HTTPException

from uuid import uuid4
import json
import random

from ..classes import (
    OnboardingLink, User,
    OnboardingTransaction, OnboardingTransactionStates,
    RegistrationRequest,
    TransactionTypes, Transaction, TransactionUpdateRequest,
    ErrorResponse
)

from ..database import SessionDep, vk

from ..config import config

router = APIRouter()

@router.get("/create", status_code=201, responses={403: {"model": ErrorResponse}})
async def create(session: SessionDep, x_self_service_token: Annotated[str | None, Header()] = None) -> OnboardingLink:
    authenticated: bool = False
    # Bypass for when self-registrations are open
    if config["server"]["registrations"]:
        authenticated = True
    # If users and onboarding links are empty, we allow it
    elif len(session.exec(select(OnboardingLink)).all()) == 0 and len(session.exec(select(User)).all()) == 0:
        authenticated = True
    # TODO: If a valid self-service token is presented, we allow it
    # garbage condition for now
    elif x_self_service_token is not None and authenticated:
        authenticated = True
    if not authenticated:
        raise HTTPException(status_code=403, detail="x-self-service-token missing or invalid")
    link: OnboardingLink = OnboardingLink(link_id=str(uuid4()))
    session.add(link)
    session.commit()
    session.refresh(link)
    print("Debug only!!!")
    print("http://localhost:8080/fe/onboard/index.html?link={}".format(link.link_id))
    return link

@router.post("/init", responses={404: {"model": ErrorResponse}})
async def init(req: RegistrationRequest, session: SessionDep) -> OnboardingTransaction:
    """Checks the validity of the onboaring link and starts an onboarding transaction"""
    l = session.get(OnboardingLink, req.link_id)
    if not l:
        raise HTTPException(status_code=404, detail="Onboarding link not found")
    tx = OnboardingTransaction.new(TransactionTypes.onboarding.value)
    session.delete(l)
    session.commit()
    return tx

@router.post("/entry", responses={404: {"model": ErrorResponse}})
def entry(rq: TransactionUpdateRequest) -> Transaction:
    """Adds the user context to the onboarding transaction"""
    k1: str = str(random.randbytes(32).hex())
    tx = Transaction.load(TransactionTypes.onboarding.value, rq.tx_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if tx.state != OnboardingTransactionStates.created.value:
        raise HTTPException(status_code=403, detail="Transaction has already been filled")
    if "username" in rq.data and "email" in rq.data:
        entry_data = {"username": rq.data["username"], "email": rq.data["email"]}
        tx.add_data(".ln", {"k1": k1})
        tx.add_private_data(".entry", entry_data)
        tx.set_state(OnboardingTransactionStates.filled.value)
    return tx

