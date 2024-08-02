from unittest.mock import Mock, patch
from ccproxy import api, tutils


class TestRemoteDeviceController:
    @patch('ccproxy.network.do_authenticated_request')
    def test_toggle(self, do_authenticated_request_mock: Mock) -> None:
        account = tutils.create_account_object()

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
        assert message in account.config.messages['bla_action']

    def test_get_supported_actions(self) -> None:
        config = {
            'messages': {
                'bla_action': ['foo', 'bar'],
                'bar_action': ['fooz']
            },
            'actions': {
                'bla_action': 'bla_action_path',
                'bar_action': 'bar_action_path'
            }
        }
        dc = api.RemoteDeviceController(tutils.create_account_object(config_override=config))

        actions = dc.get_supported_actions()
        assert actions == ('bla_action', 'bar_action',)
