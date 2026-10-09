from typing import Annotated
from fastapi import Depends

from .config import config

from sqlmodel import Field, Session, SQLModel, create_engine, select
from valkey import Valkey
from valkey.backoff import ExponentialBackoff
from valkey.retry import Retry
from valkey.exceptions import ConnectionError, TimeoutError

sqlite_url = config["database"]["sql"]["string"]
engine = create_engine(sqlite_url, echo=False)
vk = Valkey(host=config["database"]["valkey"]["host"], port=config["database"]["valkey"]["port"], db=config["database"]["valkey"]["db"], decode_responses=True, retry=Retry(ExponentialBackoff(cap=2, base=0.1), 5), retry_on_error=[ConnectionError, TimeoutError], health_check_interval=30)

async def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
