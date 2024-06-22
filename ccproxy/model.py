from pydantic import BaseModel
from typing import Optional


class CredentialsEnvelope(BaseModel):
    username: str
    password: str
    host: str


class Account(CredentialsEnvelope):
    id: Optional[str]
    cookie: Optional[str]
