from typing import Any
from pydantic import BaseModel
import random
from ccproxy import model, network


class Config(BaseModel):
    messages: dict[str, list[str]]
    actions: dict[str, str]


class RemoteDeviceController:
    class UnknownActionError(RuntimeError):
        pass

    class InvalidConfigError(RuntimeError):
        pass

    def __init__(
        self,
        config: dict[str, Any],
        account: model.Account
    ) -> None:
        self._config = Config.parse_obj(config)
        self._account = account
        self._validate_config()

    def _validate_config(self) -> None:
        missing_messages = []
        empty_messages = []
        empty_actions = []
        for action_name in self._config.actions:
            if action_name not in self._config.messages:
                missing_messages.append(action_name)
            else:
                messages = self._config.messages[action_name]
                if len(messages) == 0:
                    empty_messages.append(action_name)

            action_path = self._config.actions[action_name]
            if action_path == '':
                empty_actions.append(action_name)

        if len(missing_messages) > 0:
            raise self.InvalidConfigError(
                f'Config is missing messages for the following actions: {", ".join(missing_messages)}'
            )

        if len(empty_actions) > 0:
            raise self.InvalidConfigError(
                f'Path is empty for the following actions: {", ".join(empty_actions)}')

        if len(empty_messages) > 0:
            raise self.InvalidConfigError(
                f'Messages are not provided for the following actions: {", ".join(empty_messages)}')

    def toggle(self, action: str) -> str:
        if action not in self._config.actions:
            raise self.UnknownActionError()

        self._do_toggle_request(self._config.actions[action])

        messages = self._config.messages[action]
        return messages[random.randint(0, len(messages) - 1)]

    def _do_toggle_request(self, action: str) -> None:
        response = network.do_authenticated_request(
            self._account,
            f'{self._account.host}/SetValue',
            'POST',
            {
                'objectName': action,
                'valueName': 'Value',
                'value': 'true'
            }
        )

        response.raise_for_status()

    def get_supported_actions(self) -> tuple[str, ...]:
        return tuple(self._config.actions.keys())
