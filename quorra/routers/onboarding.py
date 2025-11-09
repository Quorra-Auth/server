from typing import Annotated

from fastapi import APIRouter, Header
from sqlmodel import select

from fastapi import HTTPException

from uuid import uuid4
import json

from ..classes import OnboardingLink, User
from ..classes import OnboardingTransaction, OnboardingTransactionStates
from ..classes import RegistrationRequest, OnboardingDataResponse
from ..classes import TransactionTypes, Transaction, TransactionUpdateRequest
from ..classes import ErrorResponse

from ..database import SessionDep
from ..database import vk

from ..utils import generate_qr
from ..utils import QRCodeResponse
from ..config import server_url
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
    token: str = str(uuid4())
    registration_details = rq.data
    tx = Transaction.load(TransactionTypes.onboarding.value, rq.tx_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if tx.state != OnboardingTransactionStates.created.value:
        raise HTTPException(status_code=403, detail="Transaction has already been filled")
    if "username" in rq.data and "email" in rq.data:
        tx.add_data({"username": rq.data["username"]}, True)
        tx.add_data({"email": rq.data["email"]}, True)
        tx.add_data({"mobile-registration-token": token}, True)
        tx.save_state(OnboardingTransactionStates.filled.value)
    return tx

@router.post("/qr", responses={404: {"model": ErrorResponse}})
def qr_gen(rq: Transaction) -> OnboardingDataResponse:
    """Generates an onboarding QR code for the frontend"""
    tx = Transaction.load(rq.tx_type.value, rq.tx_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if "mobile-registration-token" not in tx.data:
        raise HTTPException(status_code=404, detail="Mobile token is missing in transaction data")
    token = tx.data["mobile-registration-token"]
    link = "quorra+{}/mobile/register?t={}".format(server_url, token)
    qr_image = generate_qr(link)
    return OnboardingDataResponse(link=link, qr_image=qr_image)

@router.post("/finish", responses={404: {"model": ErrorResponse}})
def finish(rq: TransactionUpdateRequest) -> Transaction:
    """Debug only - finish a transaction"""
    tx = Transaction.load(TransactionTypes.onboarding.value, rq.tx_id)
    tx.save_state(OnboardingTransactionStates.finished.value)
    return tx
