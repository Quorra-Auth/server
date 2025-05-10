# This file is only kept here for reference

from typing import Union
from fastapi import APIRouter

from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

router = APIRouter()


@router.get("/hello")
async def read_root():
    return {"Hello": "World"}

@router.post("/items/")
async def create_item(item: Item):
    return item

@router.get("/items/{item_id}")
async def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
