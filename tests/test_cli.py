import json
from typing import Any
from unittest.mock import Mock, patch
import pytest
from requests import Response
from ccproxy import cli, model
import tempfile
from pydantic.error_wrappers import ValidationError

class TestCreateAccountOnServer:
    def _create_dummy_response(self, status_code: int = 200, response_body='some-id') -> Response:
        response = Mock()
        response.status_code = status_code
        response.text = response_body

        return response
    
    def _create_dummy_account(self, json_method_return_value: dict) -> model.Account:
        account = Mock()
        account.json.return_value = json.dumps(json_method_return_value)

        return account

    @patch('requests.request')
    def test_happy_path(self, mock_request: Mock) -> None:
        dummy_account_as_dict = {'foo': 'bar'}
        dummy_account = self._create_dummy_account(dummy_account_as_dict)

        mock_request.return_value = self._create_dummy_response()

        result = cli.create_account_on_server('foo-ccproxy-login-url', dummy_account)

        assert result == 'some-id'
        mock_request.assert_called_once_with(
            'POST', 
            'foo-ccproxy-login-url', 
            json=dummy_account_as_dict,
            headers={
                'Content-Type': 'application/json; charset=utf-8',
            }
        )

    @patch('requests.request')
    def test_non_200_response_returned(self, mock_request: Mock) -> None:
        dummy_account_as_dict = {'foo': 'bar'}
        dummy_account = self._create_dummy_account(dummy_account_as_dict)

        mock_request.return_value = self._create_dummy_response(
            status_code=500,
            response_body='kaput'
        )

        with pytest.raises(RuntimeError, match='Unable to create account, returned error: kaput'):
            cli.create_account_on_server('foo-ccproxy-login-url', dummy_account)

class TestCreateAccountOnServerFromFile:
    @pytest.fixture
    def account_dict(self) -> dict[str, Any]:
        return {
            'host': 'https://example.org',
            'username': 'foo-username',
            'device': {
                'device_name': 'foo-dn',
                'platform': 'foo-plt',
                'push_token': 'foo-pt'
            },
            'config': {}
        }

    @patch('ccproxy.cli.create_account_on_server')
    def test_happy_path(self, mock_create_account_on_server: Mock, account_dict: dict[str, Any]) -> None:
        with tempfile.NamedTemporaryFile() as file:
            account_json = json.dumps(account_dict)
            file.write(account_json.encode('utf-8'))
            file.seek(0)

            cli.create_account_on_server_from_file('foo-ccproxy-login-url', file.name, 'foo-password')

        mock_create_account_on_server.assert_called_once()
        call_args = mock_create_account_on_server.call_args[0]
        assert call_args[0] == 'foo-ccproxy-login-url'
        assert isinstance(call_args[1], model.Account)
        account = call_args[1] # type: model.Account
        assert account.password == 'foo-password'
        assert account.username == account_dict['username']
        assert account.host == account_dict['host']
        assert account.device.device_name == account_dict['device']['device_name']
        assert account.device.platform == account_dict['device']['platform']
        assert account.device.push_token == account_dict['device']['push_token']

    def test_file_not_exists(self) -> None:
        with pytest.raises(RuntimeError, match='File "non-existing-file" doesn\'t exist.'):
            cli.create_account_on_server_from_file(
                'foo-ccproxy-login-url',
                'non-existing-file',
                'foo-password'
            )

    @patch('ccproxy.cli.create_account_on_server')
    def test_invalid_config_given(
        self,
        mock_create_account_on_server: Mock,
        account_dict: dict[str, Any]
    ) -> None:
        del account_dict['username']

        with tempfile.NamedTemporaryFile() as file:
            account_json = json.dumps(account_dict)
            file.write(account_json.encode('utf-8'))
            file.seek(0)

            with pytest.raises(ValidationError, match='username'):
                cli.create_account_on_server_from_file(
                    'foo-ccproxy-login-url', file.name, 'foo-password'
                )

        mock_create_account_on_server.assert_not_called()