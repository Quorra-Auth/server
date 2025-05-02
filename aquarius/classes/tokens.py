from pydantic import BaseModel
from datetime import datetime

class Token(BaseModel):
    value: str
    type: str
    expiration: datetime | None

class UserRegistrationToken(Token):
    type: str = "user_registration"
