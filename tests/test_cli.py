import json
from unittest.mock import Mock, patch
import pytest
from requests import Response
from ccproxy import cli, model

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

class TestCreateAccountFromFile:
    def test_happy_path(self) -> None:
        assert False

    def test_file_not_exists(self) -> None:
        assert False

    def test_invalid_config_given(self) -> None:
        assert False