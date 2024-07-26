from pydantic import BaseModel, Field, AnyHttpUrl
from typing import Optional

# TODO define max length for all fields (to avoid clients potentially passing some crap there)

class CredentialsEnvelope(BaseModel):
    # username: str = Field(min_length=1)
    # password: str = Field(min_length=1)
    username: str
    password: str

    host: AnyHttpUrl

class Config(BaseModel):
    messages: dict[str, list[str]] = {}
    actions: dict[str, str] = {}

class Account(CredentialsEnvelope):
    id: Optional[str]
    cookie: Optional[str]
    config: Optional[Config]

class ConfigUpdatePayload(BaseModel):
    id: str
    config: Config
