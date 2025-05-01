from typing import Annotated
from fastapi import Depends
from sqlmodel import Field, Session, SQLModel, create_engine, select

sqlite_url = "sqlite:///database.db"
engine = create_engine(sqlite_url, echo=True)

async def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
