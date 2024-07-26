import random
from ccproxy import model, network


class RemoteDeviceController:
    class UnknownActionError(RuntimeError):
        pass

    def __init__(
        self,
        account: model.Account
    ) -> None:
        self._account = account

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
