from typing import Any
from unittest import mock
import pytest
from ccproxy.handlers.process_action import process_action_handler, do_api_call
from ccproxy.handlers import utils as handler_utils
from unittest.mock import patch, Mock
from ccproxy import config, api
from requests.exceptions import HTTPError


class TestProcessAction:
    def test_no_action_query_param_specified(self) -> None:
        result = process_action_handler(
            {'queryStringParameters': {}, 'headers': {}},
            {}
        )

        assert result is not None
        assert 'statusCode' in result
        assert result['statusCode'] == 400
        assert '_errorType' in result
        assert result['_errorType'] == 'action_not_specified'

    @patch('ccproxy.container.create_account_table')
    @patch('ccproxy.handlers.process_action.do_api_call')
    def test_unknown_action_given(self, mock_do_api_call: Mock, mock_create_account_table: Mock) -> None:
        account_table = Mock()
        account_table.find.return_value = {}

        mock_do_api_call.side_effect = api.RemoteDeviceController.UnknownActionError()

        mock_create_account_table.return_value = account_table

        result = process_action_handler(
            {
                'queryStringParameters': {
                    'action': 'something1234567890123456'
                },
                'headers': {
                    'x-ccproxy-account': '1234'
                }
            },
            {}
        )

        assert result is not None
        assert 'statusCode' in result
        assert result['statusCode'] == 400
        assert '_errorType' in result
        assert result['_errorType'] == 'unknown_action'
        assert result['body'] == 'Unkown action "something1234567" given.'

    @patch('ccproxy.container.create_account_table')
    def test_not_found(self, mock_create_account_table: Mock) -> Any:
        account_table = Mock()
        account_table.find.return_value = None

        mock_create_account_table.return_value = account_table

        account_id = '12345678910111223141516'

        result = process_action_handler(
            {
                'queryStringParameters': {'action': 'something'},
                'headers': {
                    'x-ccproxy-account': account_id
                }
            },
            {}
        )

        assert result is not None
        assert 'statusCode' in result
        assert result['statusCode'] == 400
        assert result['body'] == f'Unable to find account "{account_id[:config.ACCOUNT_ID_LENGTH]}".'

    @patch('ccproxy.container.create_account_table')
    @patch('ccproxy.handlers.process_action.do_api_call')
    def test_happy_path(self, mock_do_api_call: Mock, mock_create_account_table: Mock) -> None:
        account_id = '1234'
        account: dict[Any, Any] = {}

        account_table = Mock(name='account_table')
        account_table.find.return_value = account

        mock_create_account_table.return_value = account_table

        mock_do_api_call.return_value = 'some_fancy_action_returned_message'

        result = process_action_handler(
            {
                'queryStringParameters': {
                    'action': 'some_fancy_action'
                },
                'headers': {
                    'x-ccproxy-account': account_id
                }
            },
            {}
        )

        assert result is not None
        assert 'statusCode' in result
        assert result['statusCode'] == 200
        assert result['body'] == 'some_fancy_action_returned_message'
        mock_do_api_call.assert_called_once_with(
            account,
            account_table,
            'some_fancy_action'
        )

    @pytest.mark.parametrize(
        'action',
        [
            'open_garage_door',
            'open_hallway_door',
            'turn_ventilation_on',
            'turn_ventilation_off',
            'turn_guests_ventilation'
        ]
    )
    def test_reauth(self, action: str) -> None:
        refreshed_account = Mock()
        refreshed_account.username = 'foousername'

        response_mock = Mock()
        response_mock.status_code = 401

        device_controller_mock = Mock()
        device_controller_mock.toggle.side_effect = [
            HTTPError(response=response_mock),
            'toggle-result'
        ]

        authenticate_mock = Mock(name='authenticate')
        authenticate_mock.return_value = refreshed_account

        create_remote_device_controller_mock = Mock(
            name='create_remote_device_controller')
        create_remote_device_controller_mock.return_value = device_controller_mock

        account = Mock()
        account.username = 'foousername'
        account_table: dict[Any, Any] = {}

        with (
            mock.patch(
                'ccproxy.main.authenticate',
                new=authenticate_mock),
            mock.patch(
                'ccproxy.container.create_remote_device_controller',
                new=create_remote_device_controller_mock
            )
        ):
            result = do_api_call(
                account, account_table, action  # type: ignore[arg-type]
            )

            assert len(create_remote_device_controller_mock.call_args_list) == 2
            create_api_client_1st_call_args, _ = create_remote_device_controller_mock.call_args_list[
                0]
            assert create_api_client_1st_call_args == (account,)
            create_api_client_2nd_call_args, _ = create_remote_device_controller_mock.call_args_list[
                1]
            assert create_api_client_2nd_call_args == (refreshed_account,)

            assert device_controller_mock.toggle.call_count == 2
            authenticate_mock.assert_called_once_with(account, account_table)
            assert result == 'toggle-result'

    def test_generic_exception_thrown(self) -> None:
        assert hasattr(process_action_handler, 'decorators') is True
        assert handler_utils.exception_handler.__name__ in process_action_handler.decorators
