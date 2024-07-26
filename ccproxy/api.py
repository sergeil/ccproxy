import random
from ccproxy import model, network


class RemoteDeviceController:
    class UnknownActionError(RuntimeError):
        pass

    class InvalidConfigError(RuntimeError):
        pass

    def __init__(
        self,
        account: model.Account
    ) -> None:
        self._account = account
        self._validate_config()

    # TODO would be better to have this thing in Config instead
    def _validate_config(self) -> None:
        cfg = self._account.config

        missing_messages = []
        empty_messages = []
        empty_actions = []
        for action_name in cfg.actions:
            if action_name not in cfg.messages:
                missing_messages.append(action_name)
            else:
                messages = cfg.messages[action_name]
                if len(messages) == 0:
                    empty_messages.append(action_name)

            action_path = cfg.actions[action_name]
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
        if action not in self._account.config.actions:
            raise self.UnknownActionError()

        self._do_toggle_request(self._account.config.actions[action])

        messages = self._account.config.messages[action]
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
        return tuple(self._account.config.actions.keys())
