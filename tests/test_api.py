from unittest.mock import Mock, patch
from ccproxy import api, model
from typing import Any


class TestRemoteDeviceController:
    def _create_account(self, config: dict[str, Any]) -> model.Account:
        return model.Account(
            username='foo-username',
            password='foo-password',
            host='https://example.org',
            config=model.Config(**config)
        )

    @patch('ccproxy.network.do_authenticated_request')
    def test_toggle(self, do_authenticated_request_mock: Mock) -> None:
        config: dict[str, Any] = {
            "messages": {
                "bla_action": ["foo", "bar"]
            },
            "actions": {
                "bla_action": "bla_action_path"
            }
        }

        account = self._create_account(config)

        response_mock = Mock()

        do_authenticated_request_mock.return_value = response_mock

        dc = api.RemoteDeviceController(account)

        message = dc.toggle('bla_action')

        do_authenticated_request_mock.assert_called_once_with(
            account,
            'https://example.org/SetValue',
            'POST',
            {
                'objectName': 'bla_action_path',
                'valueName': 'Value',
                'value': 'true'
            }
        )
        response_mock.raise_for_status.assert_called_once()
        assert message in config['messages']['bla_action']

    def test_get_supported_actions(self) -> None:
        config = {
            "messages": {
                "bla_action": ["foo", "bar"],
                "bar_action": ["fooz"]
            },
            "actions": {
                "bla_action": "bla_action_path",
                "bar_action": "bar_action_path"
            }
        }
        dc = api.RemoteDeviceController(self._create_account(config))

        actions = dc.get_supported_actions()
        assert actions == ('bla_action', 'bar_action',)
