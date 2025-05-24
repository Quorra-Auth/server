from typing import Annotated
from fastapi import Depends

from .config import config

from sqlmodel import Field, Session, SQLModel, create_engine, select
from valkey import Valkey

sqlite_url = config["database"]["sql"]["string"]
engine = create_engine(sqlite_url, echo=True)
vk = Valkey(host=config["database"]["valkey"]["host"], port=config["database"]["valkey"]["port"], db=config["database"]["valkey"]["db"], decode_responses=True)

async def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
