from pydantic import BaseModel, Field, AnyHttpUrl, root_validator
from typing import Optional
from ccproxy import config

# TODO define max length for all fields (to avoid clients potentially passing some crap there)

ACCOUNT_ID_FIELD = Field(min_length=1, max_length=config.ACCOUNT_ID_LENGTH)

class CredentialsEnvelope(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    host: AnyHttpUrl

class Config(BaseModel):
    messages: dict[str, list[str]] = {}
    actions: dict[str, str] = {}

    @root_validator
    def validate_fields(cls, values) -> None:
        messages, actions = values.get('messages'), values.get('actions')

        missing_messages = []
        empty_messages = []
        empty_actions = []
        for action_name in actions:
            if action_name not in messages:
                missing_messages.append(action_name)
            else:
                current_action_messages = messages[action_name]
                if len(current_action_messages) == 0:
                    empty_messages.append(action_name)

            action_path = actions[action_name]
            if action_path == '':
                empty_actions.append(action_name)

        if len(missing_messages) > 0:
            raise ValueError(
                f'Missing messages for the following actions: {", ".join(missing_messages)}'
            )

        if len(empty_actions) > 0:
            raise ValueError(
                f'Path is empty for the following actions: {", ".join(empty_actions)}')

        if len(empty_messages) > 0:
            raise ValueError(
                f'Messages are not provided for the following actions: {", ".join(empty_messages)}')

        return values

class Device(BaseModel):
    device_name: str = Field(min_length=1)
    platform: str = Field(min_length=1) # TODO should be enum of iOS, Android
    push_token: str = Field(min_length=1)

class Account(CredentialsEnvelope):
    # TODO why we have fields marked as optional here?
    id: Optional[str] = ACCOUNT_ID_FIELD
    cookie: Optional[str]
    device: Device
    config: Optional[Config]

class ConfigUpdatePayload(BaseModel):
    id: str = ACCOUNT_ID_FIELD
    config: Config
